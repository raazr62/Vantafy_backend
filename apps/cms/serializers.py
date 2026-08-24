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
    OurMetrics,
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

class OurMetricsSerializer(serializers.ModelSerializer):
    metrics_list = serializers.SerializerMethodField()

    class Meta:
        model = OurMetrics
        fields = '__all__'

    def get_metrics_list(self, obj):
        return [
            {"key": "web_search", "value": obj.web_search, "label": obj.web_search_label},
            {"key": "content_creators", "value": obj.content_creators, "label": obj.content_creators_label},
            {"key": "leaks_found", "value": obj.leaks_found, "label": obj.leaks_found_label},
            {"key": "recovered", "value": obj.recovered,    "label": obj.recovered_label},
            {"key": "success_score", "value": obj.success_score, "label": obj.success_score_label},
        ]

