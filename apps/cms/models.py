from django.db import models
from django.utils.text import slugify
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache

# Cache key constant
LANDING_PAGE_CACHE_KEY = 'landing_page_sections'

class Page(models.Model):
    class Type(models.TextChoices):
        PRIVACY_POLICY = 'privacy_policy', 'Privacy Policy'
        TERMS_AND_CONDITIONS = 'terms_and_conditions', 'Terms and Conditions'
        COOKIE_POLICY = 'cookie_policy', 'Cookie Policy'
        IMPRINT = 'imprint', 'Imprint'

    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True)
    content = models.TextField()
    type = models.CharField(max_length=50, choices=Type.choices)
    status = models.BooleanField(default=True)


    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} (v{self.version})"


class CMS(models.Model):
    page = models.CharField(max_length=255, blank=True, null=True)
    section = models.CharField(max_length=255, blank=True, null=True)
    title = models.CharField(max_length=255, blank=True, null=True)
    sub_title = models.TextField(blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    short_description = models.TextField(blank=True, null=True)
    background_image = models.CharField(max_length=255, blank=True, null=True)
    file_url = models.CharField(max_length=255, blank=True, null=True)
    button_text = models.CharField(max_length=255, blank=True, null=True)
    button_link = models.CharField(max_length=255, blank=True, null=True)
    other = models.CharField(max_length=255, blank=True, null=True)

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='active'
    )

    def __str__(self):
        return self.title or 'Page'


class FAQ(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.question
    
class HeroSection(models.Model):
    title = models.CharField(max_length=255)
    subtitle = models.TextField()
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.title
    
class HeroRadarIcon(models.Model):
    icon = models.ImageField(upload_to='hero_radar_icons/')
    
    def __str__(self):
        return f"HeroRadarIcon {self.id}"
    
class RepresentPlatform(models.Model):
    name = models.CharField(max_length=255)
    icon = models.ImageField(upload_to='platforms/')
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.name
    
class AmongOurCustomer(models.Model):
    name = models.CharField(max_length=255)
    profile_pic = models.ImageField(upload_to='customers/')
    social_media_icon = models.ImageField(upload_to='customers/social_media_icons/')
    followers_count = models.IntegerField()
    status = models.BooleanField(default=True)

    def __str__(self):
        return self.name

class Testimonial(models.Model):
    name = models.CharField(max_length=255)
    profession = models.CharField(max_length=255)
    profile_pic = models.ImageField(upload_to='testimonials/')  
    rating = models.IntegerField()
    platform = models.ImageField(upload_to='testimonials/platforms/')
    review_title = models.CharField(max_length=255)
    review = models.TextField()

    def __str__(self):
        return self.name
    
class HowItWorks(models.Model):
    question = models.CharField(max_length=255)
    answer = models.TextField()
    status = models.BooleanField(default=True)
    
    def __str__(self):
        return self.question
    
class IdentityTracking(models.Model):
    title = models.CharField(max_length=255)
    short_description = models.TextField()
    image = models.ImageField(upload_to='identity_tracking/')
    
    def __str__(self):
        return self.title


# Cache Invalidation Signals

@receiver(post_save, sender=FAQ)
@receiver(post_save, sender=HeroSection)
@receiver(post_save, sender=HeroRadarIcon)
@receiver(post_save, sender=RepresentPlatform)
@receiver(post_save, sender=AmongOurCustomer)
@receiver(post_save, sender=Testimonial)
@receiver(post_save, sender=HowItWorks)
@receiver(post_save, sender=IdentityTracking)
def invalidate_landing_page_cache(sender, **kwargs):
    cache.delete(LANDING_PAGE_CACHE_KEY)

@receiver(post_delete, sender=FAQ)
@receiver(post_delete, sender=HeroSection)
@receiver(post_delete, sender=HeroRadarIcon)
@receiver(post_delete, sender=RepresentPlatform)
@receiver(post_delete, sender=AmongOurCustomer)
@receiver(post_delete, sender=Testimonial)
@receiver(post_delete, sender=HowItWorks)
@receiver(post_delete, sender=IdentityTracking)
def invalidate_landing_page_cache_on_delete(sender, **kwargs):
    cache.delete(LANDING_PAGE_CACHE_KEY)

