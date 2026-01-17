from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import ScanJob, ScanResult


@admin.register(ScanJob)
class ScanJobAdmin(ModelAdmin):
    list_display = [
        'id', 'creator_name', 'status', 
        'completed_spiders', 'total_spiders', 
        'get_total_images', 'get_total_videos',
        'created_at'
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['creator_name', 'id']
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'completed_at',
        'total_spiders', 'completed_spiders'
    ]
    ordering = ['-created_at']
    
    @admin.display(description='Total Images')
    def get_total_images(self, obj):
        return obj.total_images
    
    @admin.display(description='Total Videos')
    def get_total_videos(self, obj):
        return obj.total_videos


@admin.register(ScanResult)
class ScanResultAdmin(ModelAdmin):
    list_display = [
        'id', 'scan_job', 'website',
        'get_image_count', 'get_video_count', 'scraped_at'
    ]
    list_filter = ['website', 'scraped_at']
    search_fields = ['website', 'scan_job__creator_name']
    readonly_fields = ['id', 'scraped_at']
    ordering = ['-scraped_at']
    
    @admin.display(description='Images')
    def get_image_count(self, obj):
        return len(obj.images or [])
    
    @admin.display(description='Videos')
    def get_video_count(self, obj):
        return len(obj.videos or [])
