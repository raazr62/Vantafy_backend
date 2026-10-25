from apps.system_setting.models import AboutSystem, SocialMedia, SystemColor, ABOUT_SYSTEM_CACHE_KEY
from rest_framework.views import APIView
from rest_framework import status
from django.core.cache import cache
from apps.system_setting.serializers import AboutSystemSerializer, SocialMediaSerializer, SystemColorSerializer
from apps.utils.helpers import success, error

# Create your views here.   
class AboutSystemAPIView(APIView):
    permission_classes = []

    def get(self, request):
        cached_data = cache.get(ABOUT_SYSTEM_CACHE_KEY)
        if cached_data:
            return success(cached_data, "About system retrieved successfully (from cache).", status.HTTP_200_OK)

        about_system = AboutSystem.objects.first()
        social_info = SocialMedia.objects.all()
        active_color = SystemColor.objects.filter(is_active=True).first()
        
        if about_system:
            about_serializer = AboutSystemSerializer(about_system)
            social_serializer = SocialMediaSerializer(social_info, many=True)
            color_serializer = SystemColorSerializer(active_color).data if active_color else None
            
            data = {
                "about_system": about_serializer.data,
                "social_media": social_serializer.data,
                "system_color": color_serializer
            }
            cache.set(ABOUT_SYSTEM_CACHE_KEY, data, timeout=3600)  # 1 hour cache
            return success(data, "About system retrieved successfully.", status.HTTP_200_OK)
        
        return error(message="About system not found.", errors=None, status_code=status.HTTP_404_NOT_FOUND)


# GET SYSTEM LOGO PUBLIC
class SystemLogoPublicView(APIView):
    permission_classes = []

    def get(self, request):
        import os
        from django.conf import settings
        from django.http import HttpResponseRedirect, FileResponse

        about_system = AboutSystem.objects.first()
        if about_system and about_system.logo:
            logo_url = about_system.get_absolute_logo_url()
            if logo_url and logo_url.startswith(("http://", "https://")) and "127.0.0.1" not in logo_url and "localhost" not in logo_url:
                return HttpResponseRedirect(logo_url)
            
            # If local file storage is used
            try:
                if os.path.exists(about_system.logo.path):
                    return FileResponse(open(about_system.logo.path, "rb"), content_type="image/png")
            except Exception:
                pass

        # Check local media directory for fallback logo
        fallback_path = os.path.join(settings.MEDIA_ROOT, "system_setting", "logo", "1.png")
        if os.path.exists(fallback_path):
            return FileResponse(open(fallback_path, "rb"), content_type="image/png")

        return HttpResponseRedirect("https://midia-mixer.s3.us-east-2.amazonaws.com/system_setting/logo/1.png")

