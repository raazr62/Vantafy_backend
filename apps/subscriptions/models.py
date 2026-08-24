from django.conf import settings
from django.db import models
from django.utils.translation import get_language
from django.utils import timezone



class Feature(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Package(models.Model):

    class PackageType(models.TextChoices):
        MONTHLY = 'month', 'Monthly'
        YEARLY = 'year', 'Yearly'
        AGENCY = 'agency', 'Agency'

    features = models.ManyToManyField(Feature, blank=True, related_name='packages')
    name = models.CharField(max_length=100, blank=True, null=True)
    stripe_product_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_price_id = models.CharField(max_length=100, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    member_limit = models.IntegerField(default=0)
    link_removal_limit_per_month = models.IntegerField(default=0)
    referral_bonus_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    type = models.CharField(
        max_length=20,
        choices=PackageType.choices,
        default=PackageType.MONTHLY 
    )
    is_recommend = models.BooleanField(default=False)
    enabled = models.BooleanField(default=True)


    def __str__(self):
        return f"{self.name} - {self.get_type_display()} - {self.price} USD"


class Subscription(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='subscriptions')
    package = models.ForeignKey(Package, on_delete=models.PROTECT, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True) 
    status = models.CharField(max_length=20, choices=[
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled'),
        ('pending', 'Pending')
    ], default='pending')
    submitted_links = models.IntegerField(
        default=0, 
        help_text="Total links submitted for DMCA removal in current active subscription period"
    )
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def has_subscription(self):
        return self.status == 'active' and self.end_date is not None and self.end_date > timezone.now()

    def reset_submitted_links(self):
        self.submitted_links = 0
        self.save(update_fields=['submitted_links'])

    def can_submit_links(self, count=1):
        """
        Check if submitting `count` links would exceed the package's monthly link removal limit.
        Returns (allowed: bool, current_submitted: int, limit: int).
        """
        if not self.package:
            return False, self.submitted_links, 0
        
        limit = self.package.link_removal_limit_per_month
        if limit > 0 and (self.submitted_links + count > limit):
            return False, self.submitted_links, limit
        return True, self.submitted_links, limit

    def increment_submitted_links(self, count=1):
        self.submitted_links += count
        self.save(update_fields=['submitted_links'])

    def __str__(self):
        return f"{self.user.email} "
    

class PaymentHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    package = models.ForeignKey(Package, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_gateway = models.CharField(max_length=50, choices=[
        ('stripe', 'Stripe'),
        ('paypal', 'PayPal'),
    ])
    payment_status = models.CharField(max_length=20, choices=[
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('pending', 'Pending'),
    ])
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    paid_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.package.name}"
    
class IncomeReport(models.Model):
    total_income = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    def __str__(self):
        return f"Income Report for {self.month.strftime('%B %Y')} - Total Income: {self.total_income}"