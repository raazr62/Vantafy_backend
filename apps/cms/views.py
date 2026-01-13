from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework import status

from apps.utils.helpers import success
from .models import (
    Page,
    CMS,
    FAQ,
    HeroSection,
    RepresentPlatform,
    AmongOurCustomer,
    Testimonial,
    HowItWorks,
    IdentityTracking,
    DevicesCompatibility
)
from .serializers import (
    PageSerializer,
    CMSSerializer,
    FAQSerializer,
    HeroSectionSerializer,
    RepresentPlatformSerializer,
    AmongOurCustomerSerializer,
    TestimonialSerializer,
    HowItWorksSerializer,
    IdentityTrackingSerializer,
    DevicesCompatibilitySerializer
)

# Create your views here.
class LandingPageAllSectionOneByOneView(APIView):
    permission_classes = []

    def get(self, request):
        # Retrieve all active sections
        hero_section = HeroSection.objects.filter(status=True).first()
        faqs = FAQ.objects.filter(status=True)
        platforms = RepresentPlatform.objects.filter(status=True)
        customers = AmongOurCustomer.objects.filter(status=True)
        testimonials = Testimonial.objects.all()
        how_it_works = HowItWorks.objects.filter(status=True)
        identity_tracking = IdentityTracking.objects.all()
        devices_compatibility = DevicesCompatibility.objects.all()
        pages = Page.objects.filter(status=True)
        
        # Serialize data
        data = {
            'hero_section': HeroSectionSerializer(hero_section).data,
            'faqs': FAQSerializer(faqs, many=True).data,
            'platforms': RepresentPlatformSerializer(platforms, many=True).data,
            'customers': AmongOurCustomerSerializer(customers, many=True).data,
            'testimonials': TestimonialSerializer(testimonials, many=True).data,
            'how_it_works': HowItWorksSerializer(how_it_works, many=True).data,
            'identity_tracking': IdentityTrackingSerializer(identity_tracking, many=True).data,
            'devices_compatibility': DevicesCompatibilitySerializer(devices_compatibility, many=True).data,
            'pages': PageSerializer(pages, many=True).data,
        }
        
        return success(data=data, message="Landing page sections retrieved successfully.", status_code=status.HTTP_200_OK)