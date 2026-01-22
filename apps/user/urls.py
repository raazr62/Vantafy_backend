from django.urls import path
from rest_framework_simplejwt.views import (
    TokenRefreshView,
    TokenRefreshView,
    TokenVerifyView,
)
from .views import (
    CookieTokenRefreshView,
    CookieTokenVerifyView,
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

    # profile
    path('avatar-update/', UpdataProfileAvatarView.as_view(), name='avatar-update'),
    path('profile-update/', ProfileUpdateAPIView.as_view(), name='profile-update'),
    # niches and stage names
    path("get-niches/", GetNichesView.as_view(), name="get-niches"),
    path('add-niches-and-stage-names/', AddNichesAndStageNamesView.as_view(), name='add-niches-and-stage-names'),
    
    # customer Social Accounts
    path('add-social-accounts/', AddSocialAccountsView.as_view(), name='add-social-accounts'),
    
]
