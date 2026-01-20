import stripe
from django.conf import settings
from django.dispatch import receiver
from .models import Package
from django.db.models.signals import post_save, pre_delete

stripe.api_key = settings.STRIPE_SECRET_KEY


def get_stripe_interval(package_type):
  
    if package_type in [Package.PackageType.MONTHLY, Package.PackageType.AGENCY]:
        return 'month'
    elif package_type == Package.PackageType.YEARLY:
        return 'year'
    return 'month' 


@receiver(post_save, sender=Package)
def create_or_update_stripe_package(sender, instance, created, **kwargs):
    # Create Stripe Product if not exists
    if not instance.stripe_product_id:
        stripe_product = stripe.Product.create(
            name=instance.name,
            description=f"{instance.name} subscription package",
        )
        instance.stripe_product_id = stripe_product.id
        instance.save()

    # Create Stripe Price if not exists
    if not instance.stripe_price_id:
        stripe_price = stripe.Price.create(
            product=instance.stripe_product_id,
            currency='usd',
            unit_amount=int(instance.price * 100),
            recurring={
                'interval': get_stripe_interval(instance.type),
            }
        )
        instance.stripe_price_id = stripe_price.id
        instance.save()
    else:
        # Update existing Stripe Product & Price
        stripe_product = stripe.Product.retrieve(instance.stripe_product_id)
        stripe_price = stripe.Price.retrieve(instance.stripe_price_id)

        # Update product name if changed
        if stripe_product['name'] != instance.name:
            stripe.Product.modify(
                stripe_product.id,
                name=instance.name
            )

        # Update price if changed
        if stripe_price['unit_amount'] != int(instance.price * 100):
            # Deactivate old price
            stripe.Price.modify(instance.stripe_price_id, active=False)

            # Create new price
            new_price = stripe.Price.create(
                product=instance.stripe_product_id,
                currency='usd',
                unit_amount=int(instance.price * 100),
                recurring={
                    'interval': get_stripe_interval(instance.type),
                }
            )
            instance.stripe_price_id = new_price.id
            instance.save()


@receiver(pre_delete, sender=Package)
def delete_stripe_package(sender, instance, **kwargs):
    # Deactivate Stripe product & price on delete
    if instance.stripe_product_id:
        stripe.Product.modify(
            instance.stripe_product_id,
            active=False,
        )
    if instance.stripe_price_id:
        stripe.Price.modify(
            instance.stripe_price_id,
            active=False,
        )
