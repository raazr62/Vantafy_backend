from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import AgencyMemberList, ConnectedSocialAccount, User
from django.utils.html import format_html

@admin.register(User)
class CustomAdminClass(ModelAdmin):
    list_display = ('id', 'email', 'full_name', 'preview_user_image', 'check_is_superuser')
    list_display_links = ('id', 'email', 'full_name', 'preview_user_image', 'check_is_superuser')
    search_fields = ('email', 'full_name')


    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.exclude(id=1)

    def preview_user_image(self, obj):
        if obj.avatar:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.avatar.url)
        return "No Image"
    
    def check_is_superuser(self, obj):
        return 'YES' if obj.is_superuser else 'NO'
    

@admin.register(AgencyMemberList)
class AgencyMemberListAdmin(ModelAdmin):
    list_display = ('id', 'agency', 'name', 'preview_profile_image')
    list_display_links = ('id', 'agency', 'name', 'preview_profile_image')
    search_fields = ('agency__email', 'name')
    list_filter = ('agency',)

    def preview_profile_image(self, obj):
        if obj.profile_image:
            return format_html('<img src="{}" style="max-height: 50px; max-width: 50px;" />', obj.profile_image.url)
        return "No Image"
