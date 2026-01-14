from rest_framework import serializers
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
    
)

class PageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Page
        fields = '__all__'

class CMSSerializer(serializers.ModelSerializer):
    class Meta:
        model = CMS
        fields = '__all__'

class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = '__all__'

class HeroSectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = HeroSection
        fields = '__all__'

class RepresentPlatformSerializer(serializers.ModelSerializer):
    class Meta:
        model = RepresentPlatform
        fields = '__all__'

class AmongOurCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = AmongOurCustomer
        fields = '__all__'

class TestimonialSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonial
        fields = '__all__'

class HowItWorksSerializer(serializers.ModelSerializer):
    class Meta:
        model = HowItWorks
        fields = '__all__'

class IdentityTrackingSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdentityTracking
        fields = '__all__'

