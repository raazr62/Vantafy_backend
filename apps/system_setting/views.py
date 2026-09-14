from apps.system_setting.models import AboutSystem, SocialMedia, SystemColor
from rest_framework.views import APIView
from apps.system_setting.serializers import AboutSystemSerializer, SocialMediaSerializer, SystemColorSerializer
from apps.utils.helpers import success, error

# Create your views here.   

class AboutSystemAPIView(APIView):
    permission_classes = []

    def get(self, request):
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
            return success(data, "About system retrieved successfully.", 200)
        
        return error(message="About system not found.", errors=None, status_code=404)
