from django.shortcuts import render, HttpResponse
from django.db.models import Sum
from apps.system_setting.models import SystemColor
from apps.user.models import User
from apps.subscriptions.models import Subscription, PaymentHistory
from apps.scanner.models import (
    CustomerScanProcessing, 
    AgencyMemberScanProcessing,
    CustomerScanResultPageUrl,
    AgencyMemberScanResultPageUrl,
    CustomerScanResultImage,
    AgencyMemberScanResultImage,
)
from django.utils import timezone
from datetime import datetime

# Create your views here.

def dashboard_callback(request, context):
    now = timezone.now()

    start_of_month = now.replace(day=1)
    
    if now.month == 12:
        start_of_next_month = now.replace(year=now.year + 1, month=1, day=1)
    else:
        start_of_next_month = now.replace(month=now.month + 1, day=1)

    # Subscription Stats
    total_subscribers = Subscription.objects.filter(status='active').count()
    total_new_subscriptions = Subscription.objects.filter(
        created_at__gte=start_of_month,
        created_at__lt=start_of_next_month
    ).count()

    # Income Stats
    total_income_data = PaymentHistory.objects.filter(payment_status='success').aggregate(Sum('amount'))
    total_income = total_income_data['amount__sum'] if total_income_data['amount__sum'] else 0.00
    
    # User Stats
    total_users = User.objects.count()
    current_month_signups = User.objects.filter(
        created_at__gte=start_of_month,
        created_at__lt=start_of_next_month
    ).count()
    
    # Scanner Data 
    # Combining Customer and Agency Member scans for a total overview
    customer_scans_count = CustomerScanProcessing.objects.count()
    agency_scans_count = AgencyMemberScanProcessing.objects.count()
    total_scans = customer_scans_count + agency_scans_count

    customer_scans_running = CustomerScanProcessing.objects.filter(status='running').count()
    agency_scans_running = AgencyMemberScanProcessing.objects.filter(status='running').count()
    total_active_scans = customer_scans_running + agency_scans_running
    
    customer_scans_completed = CustomerScanProcessing.objects.filter(status='completed').count()
    agency_scans_completed = AgencyMemberScanProcessing.objects.filter(status='completed').count()
    total_completed_scans = customer_scans_completed + agency_scans_completed

    # Links & Images Stats
    total_customer_links = CustomerScanResultPageUrl.objects.count()
    total_agency_links = AgencyMemberScanResultPageUrl.objects.count()
    total_links = total_customer_links + total_agency_links

    total_submitted_links = (
        CustomerScanResultPageUrl.objects.filter(send_mail_status='submitted').count() +
        AgencyMemberScanResultPageUrl.objects.filter(send_mail_status='submitted').count()
    )

    total_customer_images = CustomerScanResultImage.objects.count()
    total_agency_images = AgencyMemberScanResultImage.objects.count()
    total_images = total_customer_images + total_agency_images

    system_color_obj = SystemColor.objects.filter(is_active=True).first()
    system_color = system_color_obj.code if system_color_obj else "#4f46e5" # Default indigo if not set

    context.update(
        {
            "system_color": system_color,
            "total_users": total_users,
            "total_subscriptions": total_subscribers,
            "total_income": total_income,
            "total_new_subscriptions": total_new_subscriptions,
            "current_month_signups": current_month_signups,
            "admins": User.objects.filter(is_staff=True).count(),
            "super_admins": User.objects.filter(is_superuser=True).count(),
            "total_scans": total_scans,
            "total_active_scans": total_active_scans,
            "total_completed_scans": total_completed_scans,
            "total_links": total_links,
            "total_submitted_links": total_submitted_links,
            "total_images": total_images,
            "data": [
                User.objects.filter(
                    created_at__year=datetime.now().year,
                    created_at__month=m
                ).count() for m in range(1, 13)
            ]
        }
    )

    return context
