from rest_framework import  serializers
from .models import (
    CustomerScanResult, 
    AgencyMemberScanResult,
    LinkRemovalRequestFromCustomer,
    LinkRemovalRequestFromAgencyMember
)

class CustomerScanResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerScanResult
        fields = '__all__'

class AgencyMemberScanResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = AgencyMemberScanResult
        fields = '__all__'


class LinkRemovalRequestFromCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = LinkRemovalRequestFromCustomer
        fields = '__all__'

class LinkRemovalRequestFromAgencyMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = LinkRemovalRequestFromAgencyMember
        fields = '__all__'

class LinkRemovalRequestSerializer(serializers.Serializer):
    links = serializers.ListField(
        child=serializers.URLField(),
        allow_empty=False
    )


class GetLinkRemovalRequestFromCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = LinkRemovalRequestFromCustomer
        fields = ['link']

class GetLinkRemovalRequestFromAgencyMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = LinkRemovalRequestFromAgencyMember
        fields = ['link']
