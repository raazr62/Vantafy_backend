from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.user.authentication import CookieJWTAuthentication
from apps.user.models import AgencyMemberList 

from .models import (
    AgencyMemberScanProcessing, CustomerScanProcessing, 
    CustomerScanResult, AgencyMemberScanResult, 
    CustomerScanResultImage, CustomerScanResultVideo, CustomerScanResultPageUrl,
    AgencyMemberScanResultImage, AgencyMemberScanResultVideo, AgencyMemberScanResultPageUrl
)
from .services import get_available_spiders, run_all_spiders_async
from apps.utils.helpers import success,error
from .serializers import CustomerScanResultSerializer, AgencyMemberScanResultSerializer

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
            print("Full Name:", full_name)

            scan_job = CustomerScanProcessing.objects.create(
                customer=user,
            )

            # Run all spiders asynchronously
            run_all_spiders_async(
                name_query='',
                job_id=scan_job.id,
                app_label='scanner',
                model_name='CustomerScanProcessing'
            )

        if role == 'agency':
            agency_member_id  = request.data.get('agency_member_id')

            if not agency_member_id:
                return Response({'error': 'agency_member_id is required'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                agency_member = AgencyMemberList.objects.get(agency=user, id=agency_member_id)
            except AgencyMemberList.DoesNotExist:
                return Response({'error': 'Agency member not found'}, status=status.HTTP_404_NOT_FOUND)

            scan_job = AgencyMemberScanProcessing.objects.create(
                agency=user,
                agency_member=agency_member,
            )


            # Run all spiders asynchronously
            run_all_spiders_async(
                name_query='',
                job_id=scan_job.id,
                app_label='scanner',
                model_name='AgencyMemberScanProcessing'
            )

        return success(data={
            'scan_job_id': str(scan_job.id),
            'status': scan_job.status,
        }, message='Scan job initiated successfully.')


class ScanResultListView(APIView):

    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]    
    
    def get(self, request):
        user = request.user
        role = user.role

        if role == 'customer':
            scan_results = CustomerScanResult.objects.filter(customer=user)
            serializer = CustomerScanResultSerializer(scan_results, many=True)
        elif role == 'agency':
            scan_results = AgencyMemberScanResult.objects.filter(agency=user)
            serializer = AgencyMemberScanResultSerializer(scan_results, many=True)

        return success(data={
            'scan_results': serializer.data,
        }, message='Scan results fetched successfully.')


class ScanResultDetailsView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]    
    
    def get(self, request, scan_result_id):
        user = request.user
        role = user.role

        serializer = None
        images = []
        videos = []
        page_urls = []

        if role == 'customer':
            try:
                scan_result = CustomerScanResult.objects.get(id=scan_result_id, customer=user)
            except CustomerScanResult.DoesNotExist:
                return error(message='Scan result not found.', status_code=status.HTTP_404_NOT_FOUND)
            
            images = CustomerScanResultImage.objects.filter(customer_scan_result=scan_result)
            videos = CustomerScanResultVideo.objects.filter(customer_scan_result=scan_result)
            page_urls = CustomerScanResultPageUrl.objects.filter(customer_scan_result=scan_result)
            serializer = CustomerScanResultSerializer(scan_result)

        elif role == 'agency':
            try:
                scan_result = AgencyMemberScanResult.objects.get(id=scan_result_id, agency=user)
            except AgencyMemberScanResult.DoesNotExist:
                return error(message='Scan result not found.', status_code=status.HTTP_404_NOT_FOUND)
            
            images = AgencyMemberScanResultImage.objects.filter(agency_member_scan_result=scan_result)
            videos = AgencyMemberScanResultVideo.objects.filter(agency_member_scan_result=scan_result)
            page_urls = AgencyMemberScanResultPageUrl.objects.filter(agency_member_scan_result=scan_result)
            serializer = AgencyMemberScanResultSerializer(scan_result)

        return success(data={
            'scan_result': serializer.data,
            'images': [img.image_url for img in images],
            'videos': [vid.video_url for vid in videos],
            'page_urls': [url.page_url for url in page_urls],
        }, message='Scan result details fetched successfully.')