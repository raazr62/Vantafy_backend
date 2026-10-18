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

