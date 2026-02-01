from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import AgencyMemberList, ConnectedSocialAccount, User
from django.utils.html import format_html

@admin.register(User)
class CustomAdminClass(ModelAdmin):
    list_display = ('id', 'email', 'full_name', 'preview_user_image', 'check_is_superuser')
    list_display_links = ('id', 'email', 'full_name', 'preview_user_image', 'check_is_superuser')
    search_fields = ('email', 'full_name')

    actions = ['send_dmca_reports_for_user']

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.exclude(id=1)

    def preview_user_image(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.avatar.url)
        return "No Image"
    
    def check_is_superuser(self, obj):
        return 'YES' if obj.is_superuser else 'NO'
    
    @admin.action(description="Send DMCA Notices for User's Active Scans")
    def send_dmca_reports_for_user(self, request, queryset):
        from apps.scanner.models import CustomerScanJob
        from apps.scanner.utils import send_dmca_notice
        
        success_count = 0
        total_jobs = 0
        
        for user in queryset:
            jobs = CustomerScanJob.objects.filter(customer=user, status='active') # Or pending? Usually active/completed.
            # Actually, results are in jobs.
            # Let's target ALL jobs for this user? Or maybe just 'active'/'completed'?
            # User wants to send notice. Usually for 'pending' items in Scans.
            jobs = CustomerScanJob.objects.filter(customer=user)
            
            for job in jobs:
                 total_jobs += 1
                 results = job.scan_results.exclude(contact_emails__isnull=True).exclude(contact_emails__exact=[])
                 for result in results:
                    collected_data = {
                        'images': result.images,
                        'videos': result.videos,
                        'page_urls': result.page_urls
                    }
                    sent, msg = send_dmca_notice(result.contact_emails, collected_data, job.creator_name)
                    if sent:
                        result.status = 'action_taken'
                        result.save()
                        success_count += 1
                        
        self.message_user(request, f"Processed {total_jobs} jobs for selected users. Sent notices for {success_count} results.")
    

@admin.register(AgencyMemberList)
class AgencyMemberListAdmin(ModelAdmin):
    list_display = ('id', 'agency', 'name', 'preview_profile_image')
    list_display_links = ('id', 'agency', 'name', 'preview_profile_image')
    search_fields = ('agency__email', 'name')
    list_filter = ('agency',)
    actions = ['send_dmca_reports_for_member']

    def preview_profile_image(self, obj):
        if obj.profile_image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.profile_image.url)
        return "No Image"

    @admin.action(description="Send DMCA Notices for Member's Active Scans")
    def send_dmca_reports_for_member(self, request, queryset):
        from apps.scanner.models import AgencyScanJob
        from apps.scanner.utils import send_dmca_notice
        
        success_count = 0
        total_jobs = 0
        
        for member in queryset:
            jobs = AgencyScanJob.objects.filter(agency_member=member)
            
            for job in jobs:
                 total_jobs += 1
                 results = job.scan_results.exclude(contact_emails__isnull=True).exclude(contact_emails__exact=[])
                 for result in results:
                    collected_data = {
                        'images': result.images,
                        'videos': result.videos,
                        'page_urls': result.page_urls
                    }
                    sent, msg = send_dmca_notice(collected_data, job.creator_name)
                    if sent:
                        result.status = 'action_taken'
                        result.save()
                        success_count += 1
                        
        self.message_user(request, f"Processed {total_jobs} jobs for selected members. Sent notices for {success_count} results.")
