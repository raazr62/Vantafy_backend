from django.contrib import admin, messages as django_messages
from django.urls import path
from django.shortcuts import render, redirect
from unfold.admin import ModelAdmin, TabularInline
from unfold.decorators import action
from apps.user.models import User
from .services import run_all_spiders_async
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
    AgencyMemberScanResultPageUrl,
    LinkRemovalRequestFromCustomer,
    LinkRemovalRequestFromAgencyMember,
    LinkRemovalVerification,
    CustomerScanUserSummary,
    AgencyMemberScanUserSummary,
)
from .tasks import enqueue_verification_for_request

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
    list_display = ('id', 'scanned_name_display', 'customer', 'status', 'progress_percentage_display', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'created_at', 'updated_at', 'completed_at')
    list_filter = ('status', 'created_at', 'updated_at')
    list_display_links =('id', 'scanned_name_display', 'customer', 'status', 'progress_percentage_display', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'created_at', 'updated_at', 'completed_at')
    search_fields = ('customer__full_name', 'customer__email', 'custom_search_name', 'error_message')
    readonly_fields = ('created_at', 'updated_at', 'completed_at', 'progress_percentage_display', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'scanned_name_display')
    actions_list = ["start_new_scan_action"]

    @action(description="Start New Scan by Name", icon="play_circle")
    def start_new_scan_action(self, request):
        return redirect("admin:scanner_customerscanprocessing_scannow")

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "scan-now/",
                self.admin_site.admin_view(self.admin_scan_now_view),
                name="scanner_customerscanprocessing_scannow",
            ),
        ]
        return custom_urls + urls

    def admin_scan_now_view(self, request):
        if request.method == "POST":
            name_to_scan = request.POST.get("name", "").strip()
            customer_id = request.POST.get("customer_id")

            if not name_to_scan:
                django_messages.error(request, "Please enter a name to scan.")
                return redirect("admin:scanner_customerscanprocessing_scannow")

            target_user = None
            if customer_id:
                try:
                    target_user = User.objects.get(id=customer_id)
                except User.DoesNotExist:
                    pass

            scan_job = CustomerScanProcessing.objects.create(
                customer=target_user,
                custom_search_name=name_to_scan
            )

            run_all_spiders_async(
                name_query=name_to_scan,
                job_id=scan_job.id,
                app_label="scanner",
                model_name="CustomerScanProcessing"
            )

            django_messages.success(
                request,
                f"Scan initiated successfully for name '{name_to_scan}' (Scan Job ID: {scan_job.id})."
            )
            return redirect("admin:scanner_customerscanprocessing_changelist")

        customers = User.objects.all().order_by("email")
        context = {
            **self.admin_site.each_context(request),
            "title": "Start New Scan by Name",
            "customers": customers,
            "opts": self.model._meta,
        }
        return render(request, "admin/scanner/scan_now.html", context)

    @admin.display(description='Scanned Name')
    def scanned_name_display(self, obj):
        return obj.search_name

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
    search_fields = ('customer__full_name', 'customer__email', 'website')
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


class CustomerScanResultInline(TabularInline):
    model = CustomerScanResult
    fk_name = 'customer'
    extra = 0
    show_change_link = True
    fields = ('website', 'status', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'created_at')
    readonly_fields = ('status', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'created_at')

    @admin.display(description='Total Images')
    def total_images_display(self, obj):
        return obj.total_images if obj else 0

    @admin.display(description='Total Videos')
    def total_videos_display(self, obj):
        return obj.total_videos if obj else 0

    @admin.display(description='Total Page URLs')
    def total_page_urls_display(self, obj):
        return obj.total_page_urls if obj else 0


@admin.register(CustomerScanUserSummary)
class CustomerScanUserSummaryAdmin(ModelAdmin):
    list_display = ('email', 'full_name', 'total_websites_display', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'last_scanned_at_display')
    list_display_links = ('email', 'full_name')
    search_fields = ('email', 'full_name')
    readonly_fields = ('email', 'full_name', 'total_websites_display', 'total_images_display', 'total_videos_display', 'total_page_urls_display')
    inlines = [CustomerScanResultInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(customer_scan_results__isnull=False).distinct()

    @admin.display(description='Total Websites Scanned')
    def total_websites_display(self, obj):
        return obj.customer_scan_results.count()

    @admin.display(description='Total Images')
    def total_images_display(self, obj):
        return sum(res.total_images for res in obj.customer_scan_results.all())

    @admin.display(description='Total Videos')
    def total_videos_display(self, obj):
        return sum(res.total_videos for res in obj.customer_scan_results.all())

    @admin.display(description='Total Page URLs')
    def total_page_urls_display(self, obj):
        return sum(res.total_page_urls for res in obj.customer_scan_results.all())

    @admin.display(description='Latest Scan')
    def last_scanned_at_display(self, obj):
        latest = obj.customer_scan_results.order_by('-created_at').first()
        return latest.created_at if latest else "-"



# -------------------------
# Inlines for Scan Result Images/Videos/URLs
# -------------------------
class CustomerScanResultImageInline(TabularInline):
    model = CustomerScanResultImage
    extra = 0
    readonly_fields = ('image_preview', 'image')
    fields = ('image_preview', 'image_url', 'image')

    @admin.display(description='Preview')
    def image_preview(self, obj):
        if not obj:
            return "No Image"
        url = obj.image.url if obj.image else obj.image_url
        if url:
            return format_html(
                '<img src="{}" style="max-width: 150px; max-height: 150px; object-fit: contain; border-radius: 4px;" />',
                url,
            )
        return "No Image"

class CustomerScanResultVideoInline(TabularInline):
    model = CustomerScanResultVideo
    extra = 0

class CustomerScanResultPageUrlInline(TabularInline):
    model = CustomerScanResultPageUrl
    extra = 0

CustomerScanResultAdmin.inlines = [
    CustomerScanResultImageInline,
    CustomerScanResultVideoInline,
    CustomerScanResultPageUrlInline
]

@admin.register(CustomerScanResultImage)
class CustomerScanResultImageAdmin(ModelAdmin):
    list_display = ('id', 'customer_scan_result', 'image_preview', 'image_url')
    search_fields = ('image_url', 'customer_scan_result__website', 'customer_scan_result__customer__email')
    readonly_fields = ('image_preview',)

    @admin.display(description='Preview')
    def image_preview(self, obj):
        if not obj:
            return "No Image"
        url = obj.image.url if obj.image else obj.image_url
        if url:
            return format_html(
                '<img src="{}" style="max-width: 150px; max-height: 150px; object-fit: contain; border-radius: 4px;" />',
                url,
            )
        return "No Image"

# -------------------------
# Agency Scan Processing
# -------------------------
@admin.register(AgencyMemberScanProcessing)
class AgencyMemberScanProcessingAdmin(ModelAdmin):
    list_display = ('id', 'scanned_name_display', 'agency', 'agency_member', 'status', 'progress_percentage_display', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'created_at', 'updated_at', 'completed_at')
    list_filter = ('status', 'created_at', 'updated_at')
    list_display_links = ('id', 'scanned_name_display', 'agency', 'agency_member', 'status', 'progress_percentage_display', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'created_at', 'updated_at', 'completed_at')
    search_fields = ('agency__full_name', 'agency__email', 'agency_member__name', 'custom_search_name', 'error_message')
    readonly_fields = ('created_at', 'updated_at', 'completed_at', 'progress_percentage_display', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'scanned_name_display')

    @admin.display(description='Scanned Name')
    def scanned_name_display(self, obj):
        return obj.search_name

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
    search_fields = ('agency__full_name', 'agency__email', 'agency_member__name', 'website')
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


class AgencyMemberScanResultInline(TabularInline):
    model = AgencyMemberScanResult
    fk_name = 'agency_member'
    extra = 0
    show_change_link = True
    fields = ('website', 'status', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'created_at')
    readonly_fields = ('website', 'status', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'created_at')

    @admin.display(description='Total Images')
    def total_images_display(self, obj):
        return obj.total_images if obj else 0

    @admin.display(description='Total Videos')
    def total_videos_display(self, obj):
        return obj.total_videos if obj else 0

    @admin.display(description='Total Page URLs')
    def total_page_urls_display(self, obj):
        return obj.total_page_urls if obj else 0


@admin.register(AgencyMemberScanUserSummary)
class AgencyMemberScanUserSummaryAdmin(ModelAdmin):
    list_display = ('name', 'agency_email_display', 'total_websites_display', 'total_images_display', 'total_videos_display', 'total_page_urls_display', 'last_scanned_at_display')
    list_display_links = ('name', 'agency_email_display')
    search_fields = ('name', 'agency__email')
    readonly_fields = ('name', 'agency_email_display', 'total_websites_display', 'total_images_display', 'total_videos_display', 'total_page_urls_display')
    inlines = [AgencyMemberScanResultInline]

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.filter(agency_member_scan_results__isnull=False).distinct()

    @admin.display(description='Agency Email')
    def agency_email_display(self, obj):
        return obj.agency.email if obj.agency else "-"

    @admin.display(description='Total Websites Scanned')
    def total_websites_display(self, obj):
        return obj.agency_member_scan_results.count()

    @admin.display(description='Total Images')
    def total_images_display(self, obj):
        return sum(res.total_images for res in obj.agency_member_scan_results.all())

    @admin.display(description='Total Videos')
    def total_videos_display(self, obj):
        return sum(res.total_videos for res in obj.agency_member_scan_results.all())

    @admin.display(description='Total Page URLs')
    def total_page_urls_display(self, obj):
        return sum(res.total_page_urls for res in obj.agency_member_scan_results.all())

    @admin.display(description='Latest Scan')
    def last_scanned_at_display(self, obj):
        latest = obj.agency_member_scan_results.order_by('-created_at').first()
        return latest.created_at if latest else "-"

class AgencyMemberScanResultImageInline(TabularInline):
    model = AgencyMemberScanResultImage
    extra = 0
    readonly_fields = ('image_preview', 'image_url', 'image')
    fields = ('image_preview', 'image_url', 'image')

    @admin.display(description='Preview')
    def image_preview(self, obj):
        if not obj:
            return "No Image"
        url = obj.image.url if obj.image else obj.image_url
        if url:
            return format_html(
                '<img src="{}" style="max-width: 150px; max-height: 150px; object-fit: contain; border-radius: 4px;" />',
                url,
            )
        return "No Image"

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

@admin.register(AgencyMemberScanResultImage)
class AgencyMemberScanResultImageAdmin(ModelAdmin):
    list_display = ('id', 'agency_member_scan_result', 'image_preview', 'image_url')
    search_fields = ('image_url', 'agency_member_scan_result__website')
    readonly_fields = ('image_preview',)

    @admin.display(description='Preview')
    def image_preview(self, obj):
        if not obj:
            return "No Image"
        url = obj.image.url if obj.image else obj.image_url
        if url:
            return format_html(
                '<img src="{}" style="max-width: 150px; max-height: 150px; object-fit: contain; border-radius: 4px;" />',
                url,
            )
        return "No Image"


@admin.register(LinkRemovalRequestFromCustomer)
class LinkRemovalRequestFromCustomerAdmin(ModelAdmin):
    list_display = ('id', 'customer', 'clickable_link', 'status', 'links')
    search_fields = ('customer__email', 'link')
    list_filter = ('customer', 'status', 'links')
    list_display_links = ('id', 'customer', 'clickable_link')
    list_editable = ('status', 'links')
    actions = ['make_pending', 'make_removed', 'make_failed', 'send_dmca_notice_action', 'run_automated_verification']

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)
        if is_new or obj.links == 'pending':
            from .tasks import enqueue_dmca_notice_for_request
            enqueue_dmca_notice_for_request(obj)
            enqueue_verification_for_request(obj)

    @admin.action(description='Send DMCA notice email for selected requests')
    def send_dmca_notice_action(self, request, queryset):
        from .tasks import enqueue_dmca_notice_for_request
        count = 0
        for obj in queryset:
            enqueue_dmca_notice_for_request(obj)
            count += 1
        self.message_user(request, f'Enqueued DMCA notice processing for {count} requests.')

    @admin.action(description='Mark selected requests as Pending')
    def make_pending(self, request, queryset):
        updated = queryset.update(status='pending')
        self.message_user(request, f'{updated} requests were successfully marked as Pending.')

    @admin.action(description='Mark selected requests as Removed')
    def make_removed(self, request, queryset):
        updated = queryset.update(status='removed')
        self.message_user(request, f'{updated} requests were successfully marked as Removed.')

    @admin.action(description='Mark selected requests as Failed')
    def make_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} requests were successfully marked as Failed.')

    @admin.action(description='Run automated verification for selected requests')
    def run_automated_verification(self, request, queryset):
        count = 0
        for obj in queryset:
            enqueue_verification_for_request(obj)
            count += 1
        self.message_user(request, f'Enqueued automated background verification for {count} links.')

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
class LinkRemovalRequestFromAgencyMemberAdmin(ModelAdmin):
    list_display = ('id', 'agency', 'agency_member', 'clickable_link', 'status', 'links')
    search_fields = ('agency__email', 'agency_member__name', 'link')
    list_filter = ('agency', 'agency_member', 'status', 'links')
    list_display_links = ('id', 'agency', 'agency_member', 'clickable_link')
    list_editable = ('status', 'links')
    actions = ['make_pending', 'make_removed', 'make_failed', 'send_dmca_notice_action', 'run_automated_verification']

    def save_model(self, request, obj, form, change):
        is_new = obj.pk is None
        super().save_model(request, obj, form, change)
        if is_new or obj.links == 'pending':
            from .tasks import enqueue_dmca_notice_for_request
            enqueue_dmca_notice_for_request(obj)
            enqueue_verification_for_request(obj)

    @admin.action(description='Send DMCA notice email for selected requests')
    def send_dmca_notice_action(self, request, queryset):
        from .tasks import enqueue_dmca_notice_for_request
        count = 0
        for obj in queryset:
            enqueue_dmca_notice_for_request(obj)
            count += 1
        self.message_user(request, f'Enqueued DMCA notice processing for {count} requests.')

    @admin.action(description='Mark selected requests as Pending')
    def make_pending(self, request, queryset):
        updated = queryset.update(status='pending')
        self.message_user(request, f'{updated} requests were successfully marked as Pending.')

    @admin.action(description='Mark selected requests as Removed')
    def make_removed(self, request, queryset):
        updated = queryset.update(status='removed')
        self.message_user(request, f'{updated} requests were successfully marked as Removed.')

    @admin.action(description='Mark selected requests as Failed')
    def make_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} requests were successfully marked as Failed.')

    @admin.action(description='Run automated verification for selected requests')
    def run_automated_verification(self, request, queryset):
        count = 0
        for obj in queryset:
            enqueue_verification_for_request(obj)
            count += 1
        self.message_user(request, f'Enqueued automated background verification for {count} links.')

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


@admin.register(LinkRemovalVerification)
class LinkRemovalVerificationAdmin(ModelAdmin):
    list_display = ('id', 'url', 'verification_status', 'http_status_code', 'retry_count', 'checked_at')
    search_fields = ('url', 'error_message')
    list_filter = ('verification_status', 'http_status_code')


    
