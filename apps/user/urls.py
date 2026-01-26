from django.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenRefreshView,
    TokenVerifyView,
)
from .views import (
    CookieTokenRefreshView,
    CookieTokenVerifyView,
    DeleteAgencyMemberDataView,
    ProfileUpdateAPIView,
    SignUpView,
    SignInView,
    SignOutView,
    ChangePasswordView,
    SendOTPView,
    ResendOTPView,
    VerifyOTPView,
    ResetPasswordView,
    UpdataProfileAvatarView,
    GetNichesView,
    AddNichesAndStageNamesView,
    AddSocialAccountsView,
    AddAgencyMemberView,
    AgencyMemberListView,
    UpdateAgencyMemberDataView,
    CreateOrDeleteNichesView,
    AddStageNameView,

    # My niches and profile
    MyNichesView,
    MyProfileView,

    # Agency Member Niches
    CreateOrUpdateAgencyMemberNichesView,
    AgencyMemberNichesView,

    # agency member stage names
    AddAgencyMemberStageNamesView,
    UpdateAgencyMemberStageNamesView,
    GetAgencyMemberStageNamesView,
    DeleteAgencyMemberStageNameView,

    # agency member social accounts
    AddAgencyMemberSocialAccountsView,
    GetAgencyMemberSocialAccountsView,
    DeleteAgencyMemberSocialAccountView,




    )

urlpatterns = [
    
    # auth
    
    path("signup/", SignUpView.as_view(), name="signup"),
    path("signin/", SignInView.as_view(), name="signin"),
    path("signout/", SignOutView.as_view(), name="signout"),
    path("token/refresh/", CookieTokenRefreshView.as_view(), name="token_refresh"),
    path("token/verify/", CookieTokenVerifyView.as_view(), name="token_verify"),

    # password
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('send-otp/', SendOTPView.as_view(), name='send-otp'),
    path('resend-otp/', ResendOTPView.as_view(), name='resend-otp'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),

    # onboarding 
    path("get-niches/", GetNichesView.as_view(), name="get-niches"),
    path('add-niches-and-stage-names/', AddNichesAndStageNamesView.as_view(), name='add-niches-and-stage-names'),

    # My account updates
    path('avatar-update/', UpdataProfileAvatarView.as_view(), name='avatar-update'),
    path('profile-update/', ProfileUpdateAPIView.as_view(), name='profile-update'),
    path('my-profile/', MyProfileView.as_view(), name='my-profile'),
    path('my-niches/', MyNichesView.as_view(), name='my-niches'),
    # niches
    path("create-or-delete-niches/", CreateOrDeleteNichesView.as_view(), name="create-or-delete-niches"),

    # state name

    path('add-stage-name/', AddStageNameView.as_view(), name='add-stage-names'),
    
    # customer Social Accounts
    path('add-social-accounts/', AddSocialAccountsView.as_view(), name='add-social-accounts'),

    # agency members

    path('add-agency-member/', AddAgencyMemberView.as_view(), name='add-agency-members'),
    path('agency-member-list/', AgencyMemberListView.as_view(), name='agency-member-list'),
    path('update-agency-member-data/<int:member_id>/', UpdateAgencyMemberDataView.as_view(), name='update-agency-member-data'),
    path('delete-agency-member/<int:member_id>/', DeleteAgencyMemberDataView.as_view(), name='delete-agency-member'),


    # Agency Member Niches
    path("create-or-update-agency-member-niches/<int:member_id>/", CreateOrUpdateAgencyMemberNichesView.as_view(), name="create-or-update-agency-member-niches"),
    path('agency-member-niches/<int:member_id>/', AgencyMemberNichesView.as_view(), name='agency-member-niches'),

    # agency member stage names

    path('add-agency-member-stage-names/<int:member_id>/', AddAgencyMemberStageNamesView.as_view(), name='add-agency-member-stage-names'),
    path('update-agency-member-stage-names/<int:stage_name_id>/', UpdateAgencyMemberStageNamesView.as_view(), name='update-agency-member-stage-names'),
    path('get-agency-member-stage-names/<int:member_id>/', GetAgencyMemberStageNamesView.as_view(), name='get-agency-member-stage-names'),
    path('delete-agency-member-stage-name/<int:stage_name_id>/', DeleteAgencyMemberStageNameView.as_view(), name='delete-agency-member-stage-name'),

    # agency member social accounts
    path('add-agency-member-social-accounts/<int:member_id>/', AddAgencyMemberSocialAccountsView.as_view(), name='add-agency-member-social-accounts'),
    path('get-agency-member-social-accounts/<int:member_id>/', GetAgencyMemberSocialAccountsView.as_view(), name='get-agency-member-social-accounts'),
    path('delete-agency-member-social-account/<int:account_id>/', DeleteAgencyMemberSocialAccountView.as_view(), name='delete-agency-member-social-account'),
    
]
