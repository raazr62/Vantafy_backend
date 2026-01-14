from django.contrib import admin
from apps.cms.models import (
    CMS, 
    FAQ,
    HeroRadarIcon, 
    Page,
    HeroSection,
    RepresentPlatform,
    AmongOurCustomer,
    Testimonial,
    HowItWorks,
    IdentityTracking,
    
)
from unfold.admin import ModelAdmin

# Register your models here.
@admin.register(Page)
class PageAdmin(ModelAdmin):
    list_display = ('id', 'title', 'slug', 'type', 'status')
    list_display_links = ('id', 'title')
    list_filter = ('type', 'status')
    search_fields = ('title', 'content')

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'content', 'type', 'status')
        }),
    )

@admin.register(CMS)
class CMSAdmin(ModelAdmin):
    pass

@admin.register(FAQ)
class FAQAdmin(ModelAdmin):
    list_display = ('id', 'question', 'status')
    list_display_links = ('id', 'question')
    list_filter = ('status',)
    search_fields = ('question', 'answer')

    fieldsets = (
        (None, {
            'fields': ('question', 'answer', 'status')
        }),
    )

@admin.register(HeroSection)
class HeroSectionAdmin(ModelAdmin):
    list_display = ('id', 'title', 'status')
    list_display_links = ('id', 'title')
    list_filter = ('status',)
    search_fields = ('title', 'subtitle')
    
@admin.register(HeroRadarIcon)
class HeroRadarIconAdmin(ModelAdmin):
    list_display = ('id', 'icon')
    list_display_links = ('id', 'icon')


@admin.register(RepresentPlatform)
class RepresentPlatformAdmin(ModelAdmin):
    list_display = ('id', 'name', 'icon', 'status')
    list_display_links = ('id', 'name')
    list_filter = ('status',)
    search_fields = ('name',)

@admin.register(AmongOurCustomer)
class AmongOurCustomerAdmin(ModelAdmin):
    list_display = ('id', 'name', 'followers_count', 'status')
    list_display_links = ('id', 'name')
    list_filter = ('status',)
    search_fields = ('name',)

@admin.register(Testimonial)
class TestimonialAdmin(ModelAdmin):
    list_display = ('id', 'name', 'profession', 'rating')
    list_display_links = ('id', 'name')
    search_fields = ('name', 'profession', 'review_title', 'review')

@admin.register(HowItWorks)
class HowItWorksAdmin(ModelAdmin):
    list_display = ('id', 'question', 'status')
    list_display_links = ('id', 'question')
    list_filter = ('status',)
    search_fields = ('question', 'answer')

@admin.register(IdentityTracking)
class IdentityTrackingAdmin(ModelAdmin):
    list_display = ('id', 'title')
    list_display_links = ('id', 'title')
    search_fields = ('title', 'short_description')

