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
        return success(data={
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
                return error(message='agency_member_id is required')

            try:
                agency_member = AgencyMemberList.objects.get(agency=user, id=agency_member_id)
            except AgencyMemberList.DoesNotExist:
                return error(message='Agency member not found')

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

class ScanRunTimeResultView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]      
    
    
    def get(self, request):
        user = request.user
        role = user.role
        
        last_scan_job = None
        scan_results = []
        
        if role == 'customer':
            last_scan_job = CustomerScanProcessing.objects.filter(customer=user).first()
 
                
        elif role == 'agency':
            agency_member_id  = request.data.get('agency_member_id')

            if not agency_member_id:
                return error(message='agency_member_id is required')

            try:
                agency_member = AgencyMemberList.objects.get(agency=user, id=agency_member_id)
            except AgencyMemberList.DoesNotExist:
                return error(message='Agency member not found')

            last_scan_job = AgencyMemberScanProcessing.objects.filter(agency_member=agency_member).first()
       
        if not last_scan_job:
            return success(data={
                'total_scanned': 0,
                'total_matched': 0,
                'total_image': 0,
                'total_videos': 0,
                'progress_percentage': 0,
                'status': 'idle',
            }, message='No scan job found.')

        total_scanned = last_scan_job.completed_spiders
        total_matched = last_scan_job.results.count()
        total_image = last_scan_job.total_images
        total_videos = last_scan_job.total_videos
        progress_percentage = last_scan_job.progress_percentage
        
        return success(data={
            'total_scanned': total_scanned,
            'total_matched': total_matched,
            'total_image': total_image,
            'total_videos': total_videos,
            'progress_percentage': progress_percentage,
            'status': last_scan_job.status,
        }, message='Scan run time results fetched successfully.')




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
            agency_member_id = request.data.get('agency_member_id')

            if not agency_member_id:
                return error(message='agency_member_id is required')

            try:
                agency_member = AgencyMemberList.objects.get(agency=user, id=agency_member_id)
            except AgencyMemberList.DoesNotExist:
                return error(message='Agency member not found')

            scan_results = AgencyMemberScanResult.objects.filter(agency=user, agency_member=agency_member)
            serializer = AgencyMemberScanResultSerializer(scan_results, many=True)
        else:
             return error(message='Invalid user role')

        # Calculate statistics
        total_number_of_site = scan_results.count()
        
        links = []
        total_images = 0
        total_videos = 0
        
        for result in scan_results:
            # Collect images
            img_urls = list(result.image_entries.values_list('image_url', flat=True))
            links.extend(img_urls)
            total_images += len(img_urls)

            # Collect videos
            vid_urls = list(result.video_entries.values_list('video_url', flat=True))
            links.extend(vid_urls)
            total_videos += len(vid_urls)

            # Collect page URLs
            p_urls = list(result.page_url_entries.values_list('page_url', flat=True))
            links.extend(p_urls)
            
        total_links = len(links)
        total_result_found = total_images + total_videos + len(links) - (total_images + total_videos) # simplified: just len(links) if links includes everything
        # Reworking calculation to be clear:
        # links list contains EVERYTHING (images, videos, pages)
        # total_result_found is the count of all those things
        
        total_result_found = len(links) 

        return success(data={
            'total_result_found': total_result_found,
            'total_number_of_site': total_number_of_site,
            'total_links': total_links,
            'links': links,
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