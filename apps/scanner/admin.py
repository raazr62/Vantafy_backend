from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import (
    CustomerScanProcessing, 
    CustomerScanResult, 
    CustomerScanResultImage, 
    CustomerScanResultVideo, 
    CustomerScanResultPageUrl, 
    UnauthorizedWebsiteAndEmail,
    AgencyMemberScanProcessing, 
    AgencyMemberScanResult,
    AgencyMemberScanResultImage,
    AgencyMemberScanResultVideo,
    AgencyMemberScanResultVideo,
    AgencyMemberScanResultPageUrl,
    LinkRemovalRequestFromCustomer,
    LinkRemovalRequestFromAgencyMember
)

from django.utils.html import format_html


@admin.register(UnauthorizedWebsiteAndEmail)
class UnauthorizedWebsiteAndEmailAdmin(ModelAdmin):
    list_display = ('website', 'email')
    search_fields = ('website', 'email')


# -------------------------
# Customer Scan Processing
# -------------------------
@admin.register(CustomerScanProcessing)
class CustomerScanProcessingAdmin(ModelAdmin):
    list_display = ('id', 'customer', 'status', 'progress_percentage_display', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'created_at', 'updated_at', 'completed_at')
    list_filter = ('status', 'created_at', 'updated_at')
    list_display_links =('id', 'customer', 'status', 'progress_percentage_display', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'created_at', 'updated_at', 'completed_at')
    search_fields = ('customer__username', 'customer__email', 'error_message')
    readonly_fields = ('created_at', 'updated_at', 'completed_at', 'progress_percentage_display', 'total_images_display', 'total_videos_display', 'total_page_urls_display')

    # Display methods for readonly fields
    @admin.display(description='Progress %')
    def progress_percentage_display(self, obj):
        return obj.progress_percentage

    @admin.display(description='Total Images')
    def total_images_display(self, obj):
        return obj.total_images

    @admin.display(description='Total Videos')
    def total_videos_display(self, obj):
        return obj.total_videos

    @admin.display(description='Total Page URLs')
    def total_page_urls_display(self, obj):
        return obj.total_page_urls


# -------------------------
# Customer Scan Result
# -------------------------
@admin.register(CustomerScanResult)
class CustomerScanResultAdmin(ModelAdmin):
    list_display = ('id', 'customer', 'website', 'status', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'created_at', 'updated_at')
    list_filter = ('status', 'website', 'created_at', 'updated_at')
    list_display_links =('id', 'customer', 'website', 'status', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'created_at', 'updated_at')
    search_fields = ('customer__username', 'customer__email', 'website')
    readonly_fields = ('created_at', 'updated_at', 'total_images_display', 'total_videos_display', 'total_page_urls_display')

    # Display methods to show related totals
    @admin.display(description='Total Images')
    def total_images_display(self, obj):
        return obj.total_images

    @admin.display(description='Total Videos')
    def total_videos_display(self, obj):
        return obj.total_videos

    @admin.display(description='Total Page URLs')
    def total_page_urls_display(self, obj):
        return obj.total_page_urls



# -------------------------
# Inlines for Scan Result Images/Videos/URLs
# -------------------------
class CustomerScanResultImageInline(TabularInline):
    model = CustomerScanResultImage
    extra = 0
    readonly_fields = ('image_url', 'image')

class CustomerScanResultVideoInline(TabularInline):
    model = CustomerScanResultVideo
    extra = 0
    readonly_fields = ('video_url',)

class CustomerScanResultPageUrlInline(TabularInline):
    model = CustomerScanResultPageUrl
    extra = 0
    readonly_fields = ('page_url',)

CustomerScanResultAdmin.inlines = [
    CustomerScanResultImageInline,
    CustomerScanResultVideoInline,
    CustomerScanResultPageUrlInline
]

# -------------------------
# Agency Scan Processing
# -------------------------
@admin.register(AgencyMemberScanProcessing)
class AgencyMemberScanProcessingAdmin(ModelAdmin):
    list_display = ('id', 'agency', 'agency_member', 'status', 'progress_percentage_display', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'created_at', 'updated_at', 'completed_at')
    list_filter = ('status', 'created_at', 'updated_at')
    list_display_links = ('id', 'agency', 'agency_member', 'status', 'progress_percentage_display', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'created_at', 'updated_at', 'completed_at')
    search_fields = ('agency__username', 'agency__email', 'agency_member__name', 'error_message')
    readonly_fields = ('created_at', 'updated_at', 'completed_at', 'progress_percentage_display', 'total_images_display', 'total_videos_display', 'total_page_urls_display')

    @admin.display(description='Progress %')
    def progress_percentage_display(self, obj):
        return obj.progress_percentage

    @admin.display(description='Total Images')
    def total_images_display(self, obj):
        return obj.total_images

    @admin.display(description='Total Videos')
    def total_videos_display(self, obj):
        return obj.total_videos

    @admin.display(description='Total Page URLs')
    def total_page_urls_display(self, obj):
        return obj.total_page_urls

# -------------------------
# Agency Scan Result
# -------------------------
@admin.register(AgencyMemberScanResult)
class AgencyMemberScanResultAdmin(ModelAdmin):
    list_display = ('id', 'agency', 'agency_member', 'website', 'status', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'created_at', 'updated_at')
    list_filter = ('status', 'website', 'created_at', 'updated_at')
    list_display_links = ('id', 'agency', 'agency_member', 'website', 'status', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'created_at', 'updated_at')
    search_fields = ('agency__username', 'agency__email', 'agency_member__name', 'website')
    readonly_fields = ('created_at', 'updated_at', 'total_images_display', 'total_videos_display', 'total_page_urls_display')

    @admin.display(description='Total Images')
    def total_images_display(self, obj):
        return obj.total_images

    @admin.display(description='Total Videos')
    def total_videos_display(self, obj):
        return obj.total_videos

    @admin.display(description='Total Page URLs')
    def total_page_urls_display(self, obj):
        return obj.total_page_urls

class AgencyMemberScanResultImageInline(TabularInline):
    model = AgencyMemberScanResultImage
    extra = 0
    readonly_fields = ('image_url', 'image')

class AgencyMemberScanResultVideoInline(TabularInline):
    model = AgencyMemberScanResultVideo
    extra = 0
    readonly_fields = ('video_url',)

class AgencyMemberScanResultPageUrlInline(TabularInline):
    model = AgencyMemberScanResultPageUrl
    extra = 0
    readonly_fields = ('page_url',)

AgencyMemberScanResultAdmin.inlines = [
    AgencyMemberScanResultImageInline,
    AgencyMemberScanResultVideoInline,
    AgencyMemberScanResultPageUrlInline
]


@admin.register(LinkRemovalRequestFromCustomer)
class LinkRemovalRequestFromCustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer', 'clickable_link')
    search_fields = ('customer__email', 'link')
    list_filter = ('customer',)
    list_display_links = ('id', 'customer', 'clickable_link')

    def clickable_link(self, obj):
        return format_html(
            '<div style="display: flex; align-items: center; gap: 8px;">'
            '<a href="{}" target="_blank">{}</a>'
            '<button type="button" onclick="var btn=this; navigator.clipboard.writeText(this.dataset.link).then(function(){{var msg=btn.nextElementSibling; msg.style.display=\'inline\'; setTimeout(function(){{msg.style.display=\'none\';}}, 2000);}})" data-link="{}" style="background: none; border: none; cursor: pointer; padding: 0; color: #555;" title="Copy to clipboard">'
            '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16" style="pointer-events: none;">'
            '<path fill-rule="evenodd" d="M4 2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V2Zm2-1a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H6ZM2 5a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1v-1h1v1a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h1v1H2Z"/>'
            '</svg>'
            '</button>'
            '<span style="display: none; font-size: 12px; color: green; margin-left: 4px;">Copied!</span>'
            '</div>',
            obj.link,
            obj.link,
            obj.link
        )

    clickable_link.short_description = "Link"

@admin.register(LinkRemovalRequestFromAgencyMember)
class LinkRemovalRequestFromAgencyMemberAdmin(admin.ModelAdmin):
    list_display = ('id', 'agency', 'agency_member', 'clickable_link')
    search_fields = ('agency__email', 'agency_member__name', 'link')
    list_filter = ('agency', 'agency_member')
    list_display_links = ('id', 'agency', 'agency_member', 'clickable_link')

    def clickable_link(self, obj):
        return format_html(
            '<div style="display: flex; align-items: center; gap: 8px;">'
            '<a href="{}" target="_blank">{}</a>'
            '<button type="button" onclick="var btn=this; navigator.clipboard.writeText(this.dataset.link).then(function(){{var msg=btn.nextElementSibling; msg.style.display=\'inline\'; setTimeout(function(){{msg.style.display=\'none\';}}, 2000);}})" data-link="{}" style="background: none; border: none; cursor: pointer; padding: 0; color: #555;" title="Copy to clipboard">'
            '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" fill="currentColor" viewBox="0 0 16 16" style="pointer-events: none;">'
            '<path fill-rule="evenodd" d="M4 2a2 2 0 0 1 2-2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V2Zm2-1a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1V2a1 1 0 0 0-1-1H6ZM2 5a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h8a1 1 0 0 0 1-1v-1h1v1a2 2 0 0 1-2 2H2a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h1v1H2Z"/>'
            '</svg>'
            '</button>'
            '<span style="display: none; font-size: 12px; color: green; margin-left: 4px;">Copied!</span>'
            '</div>',
            obj.link,
            obj.link,
            obj.link
        )

    clickable_link.short_description = "Link"

    
