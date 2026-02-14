from rest_framework import  serializers
from .models import CustomerScanResult, AgencyMemberScanResult

class CustomerScanResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerScanResult
        fields = '__all__'

class AgencyMemberScanResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgencyMemberScanResult
        fields = '__all__'


class LinkRemovalRequestSerializer(serializers.Serializer):
    links = serializers.ListField(
        child=serializers.URLField()
    )