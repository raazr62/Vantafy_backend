from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import timedelta
from django.utils import timezone
from .managers import UserManager
from django.contrib.auth.hashers import check_password



class User(AbstractBaseUser, PermissionsMixin):
    class Roles(models.TextChoices):
        CUSTOMER = 'customer', _('Customer')
        AGENCY = 'agency', _('Agency')

    email = models.EmailField(_("email address"), unique=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    role = models.CharField(max_length=20, choices=Roles.choices, default=Roles.CUSTOMER)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_superuser = models.BooleanField(default=False)
    term_and_condition_accepted = models.BooleanField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

class Niche(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='niches')
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    
class StageName(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='stage_names')
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name
    
    
class ConnectedSocialAccount(models.Model):
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='social_accounts')
    platform = models.CharField(max_length=100)
    username = models.CharField(max_length=255)

PURPOSE = (
    ('password_reset', 'Password Reset'),
    ('login', 'Login'),
    ('delete_account', 'Delete Account'),
    ('account_create', 'Account Create')
)

class OTP(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    otp = models.CharField(max_length=255)
    is_verify = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    purpose = models.CharField(max_length=50, blank=True, null=True, choices=PURPOSE) # login, password reset, 2fa etc
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(minutes=3)
        super().save(*args, **kwargs)

    def is_expired(self):
        return timezone.now() > self.expires_at

    def check_otp(self, raw_otp):
        return check_password(raw_otp, self.otp)



class AgencyMemberList(models.Model):
    agency = models.ForeignKey(User, on_delete=models.CASCADE, related_name='agency_members')
    name = models.CharField(max_length=255)
    profile_image = models.ImageField(upload_to='agency_members/', blank=True, null=True)


    def __str__(self):
        return self.name