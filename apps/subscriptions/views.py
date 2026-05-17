from asyncio.log import logger
from datetime import timedelta
import os
from rest_framework.views import APIView
import stripe

from apps.user.authentication import CookieJWTAuthentication
from apps.user.models import User
from django.http import HttpResponse
from .serializers import (
    SubscriptionPackageSerializer,
    CurrentSubscriptionSerializer,
    FeatureSerializer,
)
from .models import IncomeReport, Package, Subscription
from apps.utils.helpers import success, error
from django.utils.timezone import now
from rest_framework.permissions import IsAuthenticated
from django.conf import settings

class SubscriptionPackageAPIView(APIView):

    permission_classes = []

    def get(self, request):
        try:
            type = request.query_params.get("type", None)
            is_recommend = request.query_params.get("is_recommend", None)
            if not type or type not in ["month", "year","agency",]:
                return error(message="Invalid or missing type parameter. Must be 'month', 'year', 'agency' or 'pay_per_download'")
            
            if is_recommend and  type == 'agency':
                packages = Package.objects.filter(type=type, enabled=True, is_recommend=True)
            elif is_recommend:
                packages = Package.objects.filter(is_recommend=True, enabled=True).exclude(type=Package.PackageType.AGENCY)
            else:
                packages = Package.objects.filter(type=type, enabled=True)

            if not packages:
               return error(errors="Package list is empty", status_code=200, message="No packages found")

            serializer = SubscriptionPackageSerializer(packages, many=True)
            
            return success(serializer.data, message="Package list fetched successfully")
        except Exception as e:
            return error(message="Failed to fetch package list", errors=str(e))
        


class StripeCheckoutAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def post(self, request):
        price_id = request.data.get('price_id')
        success_url = request.data.get('success_url')
        cancel_url = request.data.get('cancel_url')
        type = request.data.get("type") 
 

        if type not in ["month", "year", "agency"]:
            return error(message="Invalid type. Must be 'month', 'year', or 'agency'")

        if not price_id or not success_url or not cancel_url:
            return error(message="Missing required parameters", errors="price_id, success_url, and cancel_url are required")

        try:
            user = request.user
            checkout_params = {
                'payment_method_types': ['card'],
                'customer_email': user.email if user.is_authenticated else None,
                'line_items': [{
                    'price': price_id,
                    'quantity': 1,
                }],
                'mode': 'subscription',
                'success_url': success_url,
                'cancel_url': cancel_url,
            }
            
            # Apply 15% referral discount coupon if user is referred and hasn't used discount yet
            if user.is_authenticated and user.referred_by and not user.has_used_referral_discount:
                referral_coupon_id = settings.STRIPE_REFERRAL_COUPON_ID  # Make sure this is set in settings
                if referral_coupon_id:
                    checkout_params['discounts'] = [{'coupon': referral_coupon_id}]

            checkout_session = stripe.checkout.Session.create(**checkout_params)

            return success(checkout_session.url, message="Stripe checkout initiated successfully")
        except Exception as e:
            return error(message="Failed to initiate Stripe checkout", errors=str(e))


class StripeWebhookAPIView(APIView):
    permission_classes = [] 

    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except ValueError as e:
            logger.error("Invalid payload: %s", str(e))
            return HttpResponse(status=400)
        except stripe.error.SignatureVerificationError as e:
            logger.error("Invalid signature: %s", str(e))
            return HttpResponse(status=400)

        try:
            if event['type'] == 'checkout.session.completed':

                session = event['data']['object']

                session_id = session.get('id')

                checkout_session = stripe.checkout.Session.retrieve(
                    session_id,
                    expand=['line_items']
                )

                customer_email = session.get('customer_email')

                user = User.objects.filter(email=customer_email).first()


                if not user:
                    return HttpResponse(status=200)

                line_items = checkout_session['line_items']['data']
                price_id = line_items[0]['price']['id'] if line_items else None
                package = Package.objects.filter(stripe_price_id=price_id).first()
                if not package:
                    return HttpResponse(status=200)

                type = package.type
                print("type:",type)

                if type == 'month':
                    duration_days = 30
                elif type == 'year':
                    duration_days = 365
                elif type == 'agency':
                    duration_days = 30
      

                if(not Subscription.objects.filter(user=user).exists()):
                    Subscription.objects.create(
                        user=user,
                        package=package,
                        stripe_subscription_id=session.get('subscription'),
                        status='active',
                        start_date=now(),
                        end_date=now() + timedelta(days=duration_days),
                    )
                else:   
                    subscription = Subscription.objects.get(user=user)
                    subscription.package = package
                    subscription.stripe_subscription_id = session.get('subscription')
                    subscription.status = 'active'
                    subscription.start_date = now()
                    subscription.end_date = now() + timedelta(days=duration_days)
                    subscription.save()



                income_report = IncomeReport.objects.first()
                if income_report is None:
                    income_report = IncomeReport.objects.create(total_income=0)

                income_report.total_income += package.price
                income_report.save()

                # Mark referred user's discount as used if they had a referral discount applied
                if user.referred_by and not user.has_used_referral_discount:
                    user.has_used_referral_discount = True
                    user.save()

                # Update referrer's earning info
                referrer = user.referred_by
                if referrer:
                    if referrer.is_verified_for_earning:
                        referrer.total_earning_amount += package.referral_bonus_percentage
                        referrer.save()
                    else:
                        counter = referrer.referral_count 
                        total_earning_month = referrer.total_earning_month
                        counter = counter - (total_earning_month * 3)
                        if counter >= 3:
                            referrer.subscriptions.end_date += timedelta(days=30)
                            referrer.total_earning_month +=1
                            referrer.save()

                        else:   
                            referrer.referral_count +=1
                            referrer.save()


        except Exception as e:
            logger.exception("Error handling Stripe webhook event: %s", str(e))
            return HttpResponse(status=500)

        return HttpResponse(status=200)  # Always return a response


class AccessStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    
    def get(self, request):
        user = request.user
        subscription = Subscription.objects.filter(user=user).first()
        if subscription and subscription.package:
            # Serialize package and its features to avoid returning a ManyRelatedManager
            package_data = SubscriptionPackageSerializer(subscription.package).data
           
            has_access = subscription.has_subscription()
            return success(
                data={
                    "has_access": has_access,
                    "subscription_package": package_data,
                },
            )

        # No subscription found
        return success(
            data={
                "has_access": False,
                "subscription_package": None,
                "subscription_features": [],
            },
            message="No active subscription",
        )


class CurrentSubscriptionPlanAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def get(self, request):
        user = request.user
        try:
            subscription = Subscription.objects.filter(user=user).first()
            if(not subscription):
                return error(message="No subscription found for the user", errors="User does not have a subscription", status_code=200)
            if subscription:
                serializer = CurrentSubscriptionSerializer(subscription)
                return success(serializer.data, message="Current subscription plan fetched successfully")
        except Exception as e:
            return error(message="Failed to fetch current subscription plan", errors=str(e))


