from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.user.authentication import CookieJWTAuthentication
from apps.user.models import AgencyMemberList

from .models import AgencyMemberScanProcessing, CustomerScanProcessing, CustomerScanResult, CustomerScanResultImage, CustomerScanResultVideo, CustomerScanResultPageUrl
from .services import get_available_spiders, run_all_spiders_async


class SpiderListView(APIView):

    permission_classes = []
    
    def get(self, request):
        spiders = get_available_spiders()
        return Response({
            'count': len(spiders),
            'spiders': spiders
        })


class ScanNowView(APIView):

    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]    
    
    def post(self, request):
        user = request.user
        role = user.role

        # Create a new CustomerScanProcessing job
        if role == 'customer':
            full_name = user.full_name

            scan_job = CustomerScanProcessing.objects.create(
                customer=user,
                creator_name=full_name
            )

            # Run all spiders asynchronously
            run_all_spiders_async(
                name_query='',
                job_id=scan_job.id,
                app_label='scanner',
                model_name='CustomerScanProcessing'
            )

        if role == 'agency':
            agency_member_name  = request.data.get('agency_member_name')

            scan_job = AgencyMemberScanProcessing.objects.create(
                agency=user,
                agency_member = AgencyMemberList.objects.get(agency=user, name=agency_member_name),
            )


            # Run all spiders asynchronously
            run_all_spiders_async(
                name_query='',
                job_id=scan_job.id,
                app_label='scanner',
                model_name='CustomerScanProcessing'
            )