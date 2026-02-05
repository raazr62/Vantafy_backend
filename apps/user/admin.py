# admin.py
from django.contrib import admin
from django.urls import path
from django.utils.translation import gettext_lazy as _
from django.db.models import Q
from unfold.admin import ModelAdmin,TabularInline

from .models import User, Niche, StageName, ConnectedSocialAccount, OTP, AgencyMemberList, AgencyMemberNiches, AgencyMemberStageNames, AgencyMemberSocialAccounts

@admin.register(User)
class UserAdmin(ModelAdmin):
    list_display = ['email', 'full_name', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'country', 'is_verified_for_earning']
    search_fields = ['email', 'full_name', 'referral_code']
    readonly_fields = ['created_at', 'updated_at', 'referral_count']
    fieldsets = (
        ('Authentication', {
            'fields': ('email', 'password')
        }),
        ('Personal Info', {
            'fields': ('full_name', 'country', 'time_zone', 'avatar')
        }),
        ('Roles & Permissions', {
            'fields': ('role', 'is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Account Status', {
            'fields': ('is_google_login', 'term_and_condition_accepted', 'is_verified_for_earning')
        }),
        ('Referral Info', {
            'fields': ('referral_code', 'referred_by', 'referral_count')
        }),
        ('Earnings', {
            'fields': ('total_earning_amount', 'total_earning_month')
        }),
        ('System Info', {
            'fields': ('created_at', 'updated_at', 'ip_address'),
            'classes': ('collapse',)
        }),
    )
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('admin-users/',
                 self.admin_site.admin_view(self.admin_users_view),
                 name='user_admin_changelist'),
            path('individual-users/',
                 self.admin_site.admin_view(self.individual_users_view),
                 name='user_individual_changelist'),
            path('agency-accounts/',
                 self.admin_site.admin_view(self.agency_accounts_view),
                 name='user_agency_changelist'),
        ]
        return custom_urls + urls
    
    def admin_users_view(self, request):
        # Show only admin users (superusers)
        self._original_view = 'admin'
        return self.changelist_view(request)
    
    def individual_users_view(self, request):
        # Show only individual/customer users
        self._original_view = 'individual'
        return self.changelist_view(request)
    
    def agency_accounts_view(self, request):
        # Show only agency accounts
        self._original_view = 'agency'
        return self.changelist_view(request)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        
        # Apply view-specific filters
        if hasattr(self, '_original_view'):
            view_type = self._original_view
            
            if view_type == 'admin':
                # Show superusers/staff as admin users
                return qs.filter(Q(is_superuser=True) | Q(is_staff=True))
            elif view_type == 'individual':
                # Show only customer role users
                return qs.filter(role=User.Roles.CUSTOMER)
            elif view_type == 'agency':
                # Show only agency role users
                return qs.filter(role=User.Roles.AGENCY)
        
        return qs
    
    def changelist_view(self, request, extra_context=None):
        # Determine which view we're in based on URL
        if 'admin-users' in request.path:
            self._original_view = 'admin'
            extra_context = extra_context or {}
            extra_context['title'] = 'Admin Users'
        elif 'individual-users' in request.path:
            self._original_view = 'individual'
            extra_context = extra_context or {}
            extra_context['title'] = 'Individual Users'
        elif 'agency-accounts' in request.path:
            self._original_view = 'agency'
            extra_context = extra_context or {}
            extra_context['title'] = 'Agency Accounts'
        
        return super().changelist_view(request, extra_context)
    
    def save_model(self, request, obj, form, change):
        # Auto-set is_staff for admin users
        if obj.is_superuser:
            obj.is_staff = True
        super().save_model(request, obj, form, change)

# Inline Admin for User's Niche
class NicheInline(TabularInline):
    model = Niche
    extra = 1

# Inline Admin for User's Stage Names
class StageNameInline(TabularInline):
    model = StageName
    extra = 1

# Inline Admin for User's Social Accounts
class ConnectedSocialAccountInline(TabularInline):
    model = ConnectedSocialAccount
    extra = 1

# Separate admin for customer details view
@admin.register(Niche)
class NicheAdmin(ModelAdmin):
    list_display = ['name', 'customer', 'customer_email']
    list_filter = ['customer__role']
    search_fields = ['name', 'customer__email']
    
    def customer_email(self, obj):
        return obj.customer.email
    customer_email.short_description = 'Customer Email'

@admin.register(StageName)
class StageNameAdmin(ModelAdmin):
    list_display = ['name', 'customer', 'is_common']
    list_filter = ['is_common', 'customer__role']

@admin.register(ConnectedSocialAccount)
class ConnectedSocialAccountAdmin(ModelAdmin):
    list_display = ['platform', 'customer']
    list_filter = ['platform', 'customer__role']

@admin.register(OTP)
class OTPAdmin(ModelAdmin):
    list_display = ['user', 'purpose', 'is_verify', 'attempts', 'created_at', 'expires_at']
    list_filter = ['purpose', 'is_verify']
    readonly_fields = ['created_at', 'expires_at']
    
    def is_expired_display(self, obj):
        return obj.is_expired()
    is_expired_display.short_description = 'Expired'
    is_expired_display.boolean = True

# Agency Member Inlines
class AgencyMemberNichesInline(TabularInline):
    model = AgencyMemberNiches
    extra = 1

class AgencyMemberStageNamesInline(TabularInline):
    model = AgencyMemberStageNames
    extra = 1

class AgencyMemberSocialAccountsInline(TabularInline):
    model = AgencyMemberSocialAccounts
    extra = 1

@admin.register(AgencyMemberList)
class AgencyMemberListAdmin(ModelAdmin):
    list_display = ['name', 'agency_email', 'niche_count', 'stage_name_count', 'social_account_count']
    list_filter = ['agency__email']
    search_fields = ['name', 'agency__email']
    inlines = [AgencyMemberNichesInline, AgencyMemberStageNamesInline, AgencyMemberSocialAccountsInline]
    
    def agency_email(self, obj):
        return obj.agency.email
    agency_email.short_description = 'Agency Email'
    
    def niche_count(self, obj):
        return obj.niches_of_agency_member.count()
    niche_count.short_description = 'Niches'
    
    def stage_name_count(self, obj):
        return obj.stage_names_of_agency_member.count()
    stage_name_count.short_description = 'Stage Names'
    
    def social_account_count(self, obj):
        return obj.social_accounts_of_agency_member.count()
    social_account_count.short_description = 'Social Accounts'

@admin.register(AgencyMemberNiches)
class AgencyMemberNichesAdmin(ModelAdmin):
    list_display = ['name', 'agency_member_name', 'agency_email']
    list_filter = ['agency_member__agency__email']
    
    def agency_member_name(self, obj):
        return obj.agency_member.name
    agency_member_name.short_description = 'Agency Member'
    
    def agency_email(self, obj):
        return obj.agency_member.agency.email
    agency_email.short_description = 'Agency Email'

@admin.register(AgencyMemberStageNames)
class AgencyMemberStageNamesAdmin(ModelAdmin):
    list_display = ['name', 'agency_member_name', 'agency_email']
    
    def agency_member_name(self, obj):
        return obj.agency_member.name
    
    def agency_email(self, obj):
        return obj.agency_member.agency.email

@admin.register(AgencyMemberSocialAccounts)
class AgencyMemberSocialAccountsAdmin(ModelAdmin):
    list_display = ['platform', 'agency_member_name', 'agency_email']
    
    def agency_member_name(self, obj):
        return obj.agency_member.name
    
    def agency_email(self, obj):
        return obj.agency_member.agency.email