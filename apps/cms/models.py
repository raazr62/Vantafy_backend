from django.db import models
from django.utils.text import slugify
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django_ckeditor_5.fields import CKEditor5Field

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
    content = CKEditor5Field("Content", config_name='full', blank=True, null=True)
    type = models.CharField(max_length=50, choices=Type.choices)
    status = models.BooleanField(default=True)


    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.type})"


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
    STATUS_CHOICE = [
        ('landing_page','Landing Page'),
        ('dashboard','Customer Dashboard')
    ]

    question = models.CharField(max_length=255, null=True, blank=True)
    answer = models.TextField(null=True, blank=True)
    type = models.CharField(max_length=100, default='landing_page', choices=STATUS_CHOICE, null=True, blank=True)
    display_order = models.PositiveIntegerField(default=1)
    status = models.BooleanField(default=True)

    class Meta:
        ordering = ['display_order']

    def __str__(self):
        return self.question or f"FAQ #{self.id}"
    
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


class OurMetrics(models.Model):
    section_title = models.CharField(max_length=255, default="Our Metrics")
    header_title = models.CharField(max_length=255, default="Numbers Matters")
    web_search = models.CharField(max_length=50, default="+55M", help_text="Web search metric value e.g. +55M")
    web_search_label = models.CharField(max_length=100, default="Web search")
    content_creators = models.CharField(max_length=50, default="+1M", help_text="Content Creators metric value e.g. +1M")
    content_creators_label = models.CharField(max_length=100, default="Content Creators")
    leaks_found = models.CharField(max_length=50, default="+55M", help_text="Leaks found metric value e.g. +55M")
    leaks_found_label = models.CharField(max_length=100, default="Leaks found")
    recovered = models.CharField(max_length=50, default="+55M", help_text="Recovered metric value e.g. +55M")
    recovered_label = models.CharField(max_length=100, default="Recovered")
    success_score = models.CharField(max_length=50, default="+100%", help_text="Success Score metric value e.g. +100%")
    success_score_label = models.CharField(max_length=100, default="Success Score")
    status = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Our Metrics"
        verbose_name_plural = "Our Metrics"

    def __str__(self):
        return f"{self.section_title} - {self.header_title}"


# Cache Invalidation Signals

@receiver(post_save, sender=FAQ)
@receiver(post_save, sender=HeroSection)
@receiver(post_save, sender=HeroRadarIcon)
@receiver(post_save, sender=RepresentPlatform)
@receiver(post_save, sender=AmongOurCustomer)
@receiver(post_save, sender=Testimonial)
@receiver(post_save, sender=HowItWorks)
@receiver(post_save, sender=IdentityTracking)
@receiver(post_save, sender=OurMetrics)
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
@receiver(post_delete, sender=OurMetrics)
def invalidate_landing_page_cache_on_delete(sender, **kwargs):
    cache.delete(LANDING_PAGE_CACHE_KEY)

