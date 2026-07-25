import logging
import stripe
from django.conf import settings
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from .models import Package

logger = logging.getLogger(__name__)


def get_stripe_interval(package_type):
    if package_type == Package.PackageType.YEARLY:
        return 'year'
    return 'month'  # MONTHLY and AGENCY use 'month'


def create_or_sync_stripe_package(instance):
    """
    Ensures the given Package has a valid Product and Price in the active Stripe account.
    If stripe_product_id or stripe_price_id are missing or invalid (e.g. from an old Stripe key/account),
    it creates new ones in Stripe and updates the Package record without triggering signals recursively.
    """
    if not instance.price or instance.price <= 0:
        return

    stripe.api_key = settings.STRIPE_SECRET_KEY
    if not stripe.api_key:
        logger.warning("Stripe secret key is not configured in settings.")
        return

    unit_amount = int(round(instance.price * 100))
    interval = get_stripe_interval(instance.type)

    product_id = instance.stripe_product_id
    price_id = instance.stripe_price_id

    # 1. Verify / Create Stripe Product
    product_exists = False
    if product_id:
        try:
            stripe_product = stripe.Product.retrieve(product_id)
            if not stripe_product.get('active', True):
                stripe.Product.modify(product_id, active=True)
            if stripe_product.name != instance.name:
                stripe.Product.modify(product_id, name=instance.name)
            product_exists = True
        except stripe.error.InvalidRequestError:
            # Product ID belongs to an old Stripe account/key or was deleted in Stripe
            product_id = None
        except stripe.error.StripeError as e:
            logger.exception("Failed to retrieve Stripe product %s: %s", product_id, e)
            return

    if not product_exists:
        try:
            stripe_product = stripe.Product.create(
                name=instance.name,
                description=f"{instance.name} subscription package",
            )
            product_id = stripe_product.id
            price_id = None  # Reset price_id since product is new
        except stripe.error.StripeError as e:
            logger.exception("Failed to create Stripe product for Package %s: %s", instance.pk, e)
            return

    # 2. Verify / Create / Update Stripe Price
    price_exists = False
    if price_id:
        try:
            stripe_price = stripe.Price.retrieve(price_id)
            price_amount = stripe_price.get('unit_amount')
            price_interval = stripe_price.get('recurring', {}).get('interval')

            if price_amount == unit_amount and price_interval == interval:
                if not stripe_price.get('active', True):
                    stripe.Price.modify(price_id, active=True)
                price_exists = True
            else:
                # Deactivate old price and create a new one (Stripe prices cannot be modified in-place)
                stripe.Price.modify(price_id, active=False)
                price_id = None
        except stripe.error.InvalidRequestError:
            # Price ID belongs to an old Stripe account/key or was deleted in Stripe
            price_id = None
        except stripe.error.StripeError as e:
            logger.exception("Failed to retrieve Stripe price %s: %s", price_id, e)
            return

    if not price_exists:
        try:
            stripe_price = stripe.Price.create(
                product=product_id,
                currency='usd',
                unit_amount=unit_amount,
                recurring={'interval': interval},
            )
            price_id = stripe_price.id
        except stripe.error.StripeError as e:
            logger.exception("Failed to create Stripe price for Package %s: %s", instance.pk, e)
            return

    # 3. Update Package in DB if IDs changed (use update() to prevent post_save recursion)
    if product_id != instance.stripe_product_id or price_id != instance.stripe_price_id:
        Package.objects.filter(pk=instance.pk).update(
            stripe_product_id=product_id,
            stripe_price_id=price_id,
        )
        instance.stripe_product_id = product_id
        instance.stripe_price_id = price_id


@receiver(post_save, sender=Package)
def create_or_update_stripe_package(sender, instance, created, **kwargs):
    create_or_sync_stripe_package(instance)


@receiver(pre_delete, sender=Package)
def delete_stripe_package(sender, instance, **kwargs):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    if instance.stripe_product_id:
        try:
            stripe.Product.modify(instance.stripe_product_id, active=False)
        except stripe.error.StripeError:
            pass
    if instance.stripe_price_id:
        try:
            stripe.Price.modify(instance.stripe_price_id, active=False)
        except stripe.error.StripeError:
            pass