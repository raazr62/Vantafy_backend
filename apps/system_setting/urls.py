from django.urls import path
from django.conf.urls.static import static
from project import settings

from .views import (
    AboutSystemAPIView,
    SystemLogoPublicView,
)

urlpatterns = [
    path("about-system/", AboutSystemAPIView.as_view(), name="about_system"),
    path("about-system/logo/", SystemLogoPublicView.as_view(), name="about_system_logo"),
    path("system-logo/", SystemLogoPublicView.as_view(), name="system_logo"),
]

