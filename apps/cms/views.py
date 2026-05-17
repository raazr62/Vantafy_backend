from rest_framework.views import APIView
from rest_framework import status
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator

from apps.utils.helpers import success
from .models import (

    FAQ,
    HeroSection,
    HeroRadarIcon,
    RepresentPlatform,
    AmongOurCustomer,
    Testimonial,
    HowItWorks,
    IdentityTracking,
    
    
)
from .serializers import (
    FAQSerializer,
    HeroSectionSerializer,
    RepresentPlatformSerializer,
    AmongOurCustomerSerializer,
    TestimonialSerializer,
    HowItWorksSerializer,
    IdentityTrackingSerializer,
    
)

# Create your views here.
class LandingPageAllSectionOneByOneView(APIView):
    permission_classes = []

    def get(self, request):
        # Generate cache key
        cache_key = 'landing_page_sections'
        
        # Try to get data from cache first
        cached_data = cache.get(cache_key)
        
        if cached_data:
            # Return cached data
            return success(data=cached_data, message="Landing page sections retrieved successfully (from cache).", status_code=status.HTTP_200_OK)
        
        # If cache miss, fetch from database
        hero_section = HeroSection.objects.filter(status=True).first()
        hero_radar_icons = HeroRadarIcon.objects.all()
        faqs = FAQ.objects.filter(status=True)
        platforms = RepresentPlatform.objects.filter(status=True)
        customers = AmongOurCustomer.objects.filter(status=True)
        testimonials = Testimonial.objects.all()
        how_it_works = HowItWorks.objects.filter(status=True)
        identity_tracking = IdentityTracking.objects.all()
        
        # Serialize data
        data = {
            'hero_section': HeroSectionSerializer(hero_section).data,
            'hero_radar_icons': [icon.icon.url for icon in hero_radar_icons],
            'faqs': FAQSerializer(faqs, many=True).data,
            'platforms': RepresentPlatformSerializer(platforms, many=True).data,
            'customers': AmongOurCustomerSerializer(customers, many=True).data,
            'testimonials': TestimonialSerializer(testimonials, many=True).data,
            'how_it_works': HowItWorksSerializer(how_it_works, many=True).data,
            'identity_tracking': IdentityTrackingSerializer(identity_tracking, many=True).data,
        }
        
        # Store in cache for 1 hour (3600 seconds)
        cache.set(cache_key, data, 3600)
        
        return success(data=data, message="Landing page sections retrieved successfully.", status_code=status.HTTP_200_OK)