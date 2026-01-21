from rest_framework import serializers
from .models import AboutSystem, SocialMedia

class AboutSystemSerializer(serializers.ModelSerializer):
    class Meta:
        model = AboutSystem
        fields = "__all__"

class SocialMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialMedia
        fields = "__all__"