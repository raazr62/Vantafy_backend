from rest_framework import serializers
from .models import ScanJob, ScanResult


class ScanResultSerializer(serializers.ModelSerializer):
    """Serializer for individual scan results."""
    
    image_count = serializers.SerializerMethodField()
    video_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ScanResult
        fields = [
            'id', 'website', 'images', 'videos',
            'image_count', 'video_count', 'scraped_at'
        ]
        read_only_fields = ['id', 'scraped_at']
    
    def get_image_count(self, obj):
        return len(obj.images or [])
    
    def get_video_count(self, obj):
        return len(obj.videos or [])


class ScanJobListSerializer(serializers.ModelSerializer):
    """Serializer for listing scan jobs (without full results)."""
    
    progress_percentage = serializers.ReadOnlyField()
    total_images = serializers.ReadOnlyField()
    total_videos = serializers.ReadOnlyField()
    result_count = serializers.SerializerMethodField()
    
    class Meta:
        model = ScanJob
        fields = [
            'id', 'creator_name', 'status',
            'total_spiders', 'completed_spiders', 'progress_percentage',
            'total_images', 'total_videos', 'result_count',
            'created_at', 'completed_at'
        ]
        read_only_fields = ['id', 'status', 'created_at', 'completed_at']
    
    def get_result_count(self, obj):
        return obj.results.count()


class ScanJobDetailSerializer(serializers.ModelSerializer):
    """Serializer for scan job details with results."""
    
    results = ScanResultSerializer(many=True, read_only=True)
    progress_percentage = serializers.ReadOnlyField()
    total_images = serializers.ReadOnlyField()
    total_videos = serializers.ReadOnlyField()
    
    class Meta:
        model = ScanJob
        fields = [
            'id', 'creator_name', 'status',
            'total_spiders', 'completed_spiders', 'progress_percentage',
            'total_images', 'total_videos',
            'created_at', 'updated_at', 'completed_at',
            'error_message', 'results'
        ]
        read_only_fields = ['id', 'status', 'created_at', 'updated_at', 'completed_at']


class CreateScanSerializer(serializers.Serializer):
    """Serializer for creating a new scan job."""
    
    creator_name = serializers.CharField(
        max_length=255,
        required=True,
        help_text="Name of the creator to search for"
    )
    
    def validate_creator_name(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Creator name must be at least 2 characters.")
        return value