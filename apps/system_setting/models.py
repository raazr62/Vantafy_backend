from django.db import models

# Create your models here.

class AboutSystem(models.Model):
    name = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    email = models.EmailField()
    copyright = models.CharField(max_length=255)
    logo = models.ImageField(upload_to='about_system/logo/', blank=True, null=True)
    favicon = models.ImageField(upload_to='about_system/favicon/', blank=True, null=True)
    description = models.TextField()

    def get_absolute_logo_url(self):
        if self.logo:
            url = self.logo.url
            if url.startswith(('http://', 'https://')):
                return url
            from django.conf import settings
            domain = getattr(settings, 'SITE_DOMAIN', None) or getattr(settings, 'BACKEND_URL', None) or 'http://127.0.0.1:8000'
            if not domain.startswith('http'):
                domain = f'http://{domain}'
            return f"{domain.rstrip('/')}{url}"
        return None

    def __str__(self):
        return self.title

class DynamicPages(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.title

class SMTPSetting(models.Model):
    ENCRYPTION_CHOICES = [
        ('none', 'None'),
        ('tls', 'TLS'),
        ('ssl', 'SSL'),
    ]

    host = models.CharField(max_length=255)
    port = models.PositiveIntegerField()
    username = models.EmailField()
    password = models.CharField(max_length=255)
    encryption = models.CharField(max_length=10, choices=ENCRYPTION_CHOICES, default='tls')
    sender_name = models.CharField(max_length=255, blank=True, null=True)
    sender_email = models.EmailField()
    is_active = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.host} ({self.sender_email})"
    
    def get_email_backend_settings(self):
        return {
            'EMAIL_HOST': self.host,
            'EMAIL_PORT': self.port,
            'EMAIL_HOST_USER': self.username,
            'EMAIL_HOST_PASSWORD': self.password,
            'EMAIL_USE_TLS': self.encryption == 'tls',
            'EMAIL_USE_SSL': self.encryption == 'ssl',
        }


class SocialMedia(models.Model):
    name = models.CharField(max_length=255)
    url = models.URLField()
    icon = models.ImageField(upload_to='about_system/social_media/', blank=True, null=True)


class SystemColor(models.Model):
    name = models.CharField(max_length=255)
    code = models.CharField(max_length=7)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


# Cache Invalidation Signals
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

ABOUT_SYSTEM_CACHE_KEY = 'about_system_data'

@receiver(post_save, sender=AboutSystem)
@receiver(post_save, sender=SocialMedia)
@receiver(post_save, sender=SystemColor)
def invalidate_about_system_cache(sender, **kwargs):
    cache.delete(ABOUT_SYSTEM_CACHE_KEY)

@receiver(post_delete, sender=AboutSystem)
@receiver(post_delete, sender=SocialMedia)
@receiver(post_delete, sender=SystemColor)
def invalidate_about_system_cache_on_delete(sender, **kwargs):
    cache.delete(ABOUT_SYSTEM_CACHE_KEY)