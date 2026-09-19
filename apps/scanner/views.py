from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from apps.user.authentication import CookieJWTAuthentication
from apps.user.models import AgencyMemberList, User

from apps.subscriptions.models import Subscription
from .models import (
    AgencyMemberScanProcessing, CustomerScanProcessing, 
    CustomerScanResult, AgencyMemberScanResult, 
    CustomerScanResultImage, CustomerScanResultVideo, CustomerScanResultPageUrl,
    AgencyMemberScanResultImage, AgencyMemberScanResultVideo, AgencyMemberScanResultPageUrl,
    LinkRemovalRequestFromCustomer, LinkRemovalRequestFromAgencyMember
)
from .services import get_available_spiders, run_all_spiders_async
from apps.utils.helpers import success,error
from .serializers import (
    CustomerScanResultSerializer, 
    AgencyMemberScanResultSerializer, 
    LinkRemovalRequestFromCustomerSerializer, 
    LinkRemovalRequestFromAgencyMemberSerializer,
    LinkRemovalRequestSerializer,
    GetLinkRemovalRequestFromCustomerSerializer,
    GetLinkRemovalRequestFromAgencyMemberSerializer
)

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
        role = getattr(user, 'role', '')

        custom_name = request.data.get('name') or request.data.get('name_query') or request.data.get('search_name')
        if custom_name:
            custom_name = str(custom_name).strip()

        # Handle Admin / Staff users
        if user.is_staff or user.is_superuser or role == 'admin':
            customer_id = request.data.get('customer_id') or request.data.get('user_id')
            target_user = None
            if customer_id:
                try:
                    target_user = User.objects.get(id=customer_id)
                except User.DoesNotExist:
                    return error(message='Selected customer user not found')

            name_to_scan = custom_name
            if not name_to_scan and target_user:
                name_to_scan = getattr(target_user, 'full_name', '') or getattr(target_user, 'username', '')

            if not name_to_scan:
                return error(message='Name is required to run scan')

            scan_job = CustomerScanProcessing.objects.create(
                customer=target_user,
                custom_search_name=name_to_scan
            )

            run_all_spiders_async(
                name_query=name_to_scan,
                job_id=scan_job.id,
                app_label='scanner',
                model_name='CustomerScanProcessing'
            )

            return success(data={
                'scan_job_id': str(scan_job.id),
                'status': scan_job.status,
                'scanned_name': name_to_scan,
                'is_member': target_user is not None,
            }, message='Admin scan job initiated successfully.')

        # Handle Customer role
        if role == 'customer':
            name_to_scan = custom_name or getattr(user, 'full_name', '')

            scan_job = CustomerScanProcessing.objects.create(
                customer=user,
                custom_search_name=custom_name if custom_name else None
            )

            run_all_spiders_async(
                name_query=name_to_scan,
                job_id=scan_job.id,
                app_label='scanner',
                model_name='CustomerScanProcessing'
            )

            return success(data={
                'scan_job_id': str(scan_job.id),
                'status': scan_job.status,
                'scanned_name': name_to_scan,
            }, message='Scan job initiated successfully.')

        # Handle Agency role
        if role == 'agency':
            agency_member_id = request.data.get('agency_member_id')

            if not agency_member_id:
                return error(message='agency_member_id is required')

            try:
                agency_member = AgencyMemberList.objects.get(agency=user, id=agency_member_id)
            except AgencyMemberList.DoesNotExist:
                return error(message='Agency member not found')

            name_to_scan = custom_name or getattr(agency_member, 'name', '')

            scan_job = AgencyMemberScanProcessing.objects.create(
                agency=user,
                agency_member=agency_member,
                custom_search_name=custom_name if custom_name else None
            )

            run_all_spiders_async(
                name_query=name_to_scan,
                job_id=scan_job.id,
                app_label='scanner',
                model_name='AgencyMemberScanProcessing'
            )

            return success(data={
                'scan_job_id': str(scan_job.id),
                'status': scan_job.status,
                'scanned_name': name_to_scan,
            }, message='Scan job initiated successfully.')

        return error(message='Invalid user role for scanning')

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
            agency_member_id  = request.query_params.get('agency_member_id')

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
            agency_member_id  = request.query_params.get('agency_member_id')


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

       


from .tasks import enqueue_dmca_notice_for_request, enqueue_verification_for_request


class LinkRemovalRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LinkRemovalRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        links = serializer.validated_data['links']
        user = request.user

        role = user.role

        if role == 'agency':
            agency_member_id = request.query_params.get('agency_member_id')

            if not agency_member_id:
                return error(message='agency_member_id is required')

            try:
                agency_member = AgencyMemberList.objects.get(agency=user, id=agency_member_id)
            except AgencyMemberList.DoesNotExist:
                return error(message='Agency member not found')

        if user.is_staff or user.is_superuser or role == 'admin':
            customer_id = request.data.get('customer_id') or request.data.get('user_id')
            target_user = user
            if customer_id:
                try:
                    target_user = User.objects.get(id=customer_id)
                except User.DoesNotExist:
                    return error(message='Selected customer user not found')

            for link in links:
                obj = LinkRemovalRequestFromCustomer.objects.create(customer=target_user, link=link)
                # Change status from 'pending' to 'requested'
                CustomerScanResultPageUrl.objects.filter(
                    customer_scan_result__customer=target_user,
                    page_url=link
                ).update(send_mail_status='requested')
                enqueue_verification_for_request(obj)

        elif role == 'customer':
            for link in links:
                obj = LinkRemovalRequestFromCustomer.objects.create(customer=user, link=link)
                # Change status from 'pending' to 'requested'
                CustomerScanResultPageUrl.objects.filter(
                    customer_scan_result__customer=user,
                    page_url=link
                ).update(send_mail_status='requested')
                enqueue_verification_for_request(obj)

        elif role == 'agency':
            for link in links:
                obj = LinkRemovalRequestFromAgencyMember.objects.create(
                    agency=user, agency_member=agency_member, link=link
                )
                # Change status from 'pending' to 'requested'
                AgencyMemberScanResultPageUrl.objects.filter(
                    agency_member_scan_result__agency_member=agency_member,
                    page_url=link
                ).update(send_mail_status='requested')
                enqueue_verification_for_request(obj)

        return success(data=[], message='Links submitted successfully.')


class LinkRemovalRequestListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def get(self, request):
        user = request.user
        role = user.role

        if role == 'customer':
            link_removal_requests = LinkRemovalRequestFromCustomer.objects.filter(customer=user)
            serializer = GetLinkRemovalRequestFromCustomerSerializer(link_removal_requests, many=True)
        elif role == 'agency':
            agency_member_id = request.query_params.get('agency_member_id')

            if not agency_member_id:
                return error(message='agency_member_id is required')

            try:
                agency_member = AgencyMemberList.objects.get(agency=user, id=agency_member_id)
            except AgencyMemberList.DoesNotExist:
                return error(message='Agency member not found')
            
            link_removal_requests = LinkRemovalRequestFromAgencyMember.objects.filter(agency=user, agency_member=agency_member)
            serializer = GetLinkRemovalRequestFromAgencyMemberSerializer(link_removal_requests, many=True)
        else:
            return error(message='Invalid user role')

        return success(data=serializer.data, message='Link removal requests fetched successfully.')





class DashboardDataAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def get(self, request):
        user = request.user
        role = user.role

        if role == 'customer':
            # --- Customer Logic ---
            # 1. Total Photos & Videos
            name = user.full_name
            avatar = user.avatar.url if user.avatar else None
            scan_results = CustomerScanResult.objects.filter(customer=user)
            
            total_photo = 0
            total_video = 0
            infringing_sites_count = scan_results.count() # Each result is one website/spider

            for res in scan_results:
                total_photo += res.total_images
                total_video += res.total_videos
            
            total_media = total_photo + total_video

            # Avoid division by zero
            if total_media > 0:
                photo_percentage = round((total_photo / total_media) * 100, 2)
                video_percentage = round((total_video / total_media) * 100, 2)
            else:
                photo_percentage = 0
                video_percentage = 0
            
            # 2. Potential Revenue
            # Formula: (total_photo + total_video) * .721
            potential_revenue = total_media * .721
            
            # 3. Link Removal Requests
            removal_requests = LinkRemovalRequestFromCustomer.objects.filter(customer=user)
            number_of_delivered_site = removal_requests.count()
            number_of_full_deleted_site = removal_requests.filter(status='removed').count()
            
            # 4. Monthly Limits
            # Get current subscription package limits
            try:
                subscription = user.subscriptions.filter(status='active').first()
                if subscription and subscription.package:
                    monthly_limit = subscription.package.link_removal_limit_per_month
                else:
                    monthly_limit = 0 # Or some default for free tier?
            except Exception:
                monthly_limit = 0

            # Count requests created THIS MONTH
            from django.utils import timezone
            now = timezone.now()
            start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            
            requests_this_month = removal_requests.filter(created_at__gte=start_of_month).count()
            
            remaining_links_to_removal = max(0, monthly_limit - requests_this_month)
            
            monthly_limit_reach = 0
            if monthly_limit > 0:
                monthly_limit_reach = round((requests_this_month / monthly_limit) * 100, 2)


            data = {
                'total_photo': total_photo,
                'photo_percentage': photo_percentage,
                'total_video': total_video,
                'video_percentage': video_percentage,
                'total_media': total_media,
                'potential_revenue': potential_revenue,
                'infringing_sites': infringing_sites_count,
                'number_of_delivered_site': number_of_delivered_site,
                'number_of_full_deleted_site': number_of_full_deleted_site,
                'deleted_sites_links': number_of_full_deleted_site, # Using count as per variable name implication in context of numbers
                'monthly_limit_reach': monthly_limit_reach,
                'remaining_links_to_removal': remaining_links_to_removal,
                'name': name,
                'avatar': avatar
            }
            return success(data=data, message='Dashboard data fetched successfully.')


        elif role == 'agency':
            # --- Agency Logic ---
            agency_member_id = request.query_params.get('agency_member_id')

            if not agency_member_id:
                return error(message='agency_member_id is required')

            try:
                agency_member = AgencyMemberList.objects.get(agency=user, id=agency_member_id)
                
                name = agency_member.name
                avatar = agency_member.profile_image.url if agency_member.profile_image else None
                
                # 1. Total Photos & Videos
                scan_results = AgencyMemberScanResult.objects.filter(agency=user, agency_member=agency_member)

                total_photo = 0
                total_video = 0
                infringing_sites_count = scan_results.count()

                for res in scan_results:
                    total_photo += res.total_images
                    total_video += res.total_videos
                
                total_media = total_photo + total_video
                
                if total_media > 0:
                    photo_percentage = round((total_photo / total_media) * 100, 2)
                    video_percentage = round((total_video / total_media) * 100, 2)
                else:
                    photo_percentage = 0
                    video_percentage = 0
                
                # 2. Potential Revenue
                potential_revenue = total_media * 2.5

                # 3. Link Removal Requests
                # Agency requests are linked to agency AND agency_member
                removal_requests = LinkRemovalRequestFromAgencyMember.objects.filter(agency=user, agency_member=agency_member)
                number_of_delivered_site = removal_requests.count()
                number_of_full_deleted_site = removal_requests.filter(status='removed').count()

                # 4. Monthly Limits (Likely based on AGENCY subscription, not member?)
                # If limits are per-member or shared, that needs clarification. 
                # Assuming limits are per AGENT (user), but shared across members? 
                # OR maybe agency has a huge limit.
                # Let's assume we check the AGENCY's subscription.
                
                try:
                    subscription = user.subscriptions.filter(status='active').first()
                    if subscription and subscription.package:
                        monthly_limit = subscription.package.link_removal_limit_per_month
                    else:
                        monthly_limit = 0
                except Exception:
                    monthly_limit = 0

                # Count requests created THIS MONTH by THIS AGENCY (all members? or just this one?)
                # User prompt implies dashboard for this member. 
                # But limits usually apply to the subscriber (Agency).
                # Logic: Show limits usage for this MEMBER specifically? Or Agency total?
                # Variable context: 'monthly_limit_reach' usually implies the constraint on the account.
                # However, if I filter by member, I show member's usage. 
                # Let's show THIS MEMBER'S usage against the AGENCY'S total limit? Or just usage?
                
                # Implementation: Show usage for this member, but limit is likely global. 
                # To be safe/simple: Show stats for this member. Limit calculation might be tricky if shared.
                # Let's count *Agency's total usage* for the limit percentage, but *Member's usage* for the raw numbers?
                # Actually, `remaining_links_to_removal` is critical.
                
                from django.utils import timezone
                now = timezone.now()
                start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

                # Total agency usage this month (all members)
                total_agency_requests_this_month = LinkRemovalRequestFromAgencyMember.objects.filter(
                    agency=user, 
                    created_at__gte=start_of_month
                ).count()

                requests_this_month_member = removal_requests.filter(created_at__gte=start_of_month).count()

                # Remaining is global for the agency
                remaining_links_to_removal = max(0, monthly_limit - total_agency_requests_this_month)
                
                monthly_limit_reach_global = 0
                if monthly_limit > 0:
                    monthly_limit_reach_global = round((total_agency_requests_this_month / monthly_limit) * 100, 2)
                
                items = {
                    'total_photo': total_photo,
                    'photo_percentage': photo_percentage,
                    'total_video': total_video,
                    'video_percentage': video_percentage,
                    'total_media': total_media,
                    'potential_revenue': potential_revenue,
                    'infringing_sites': infringing_sites_count,
                    'number_of_delivered_site': number_of_delivered_site,
                    'number_of_full_deleted_site': number_of_full_deleted_site,
                    'deleted_sites_links': number_of_full_deleted_site,
                    'monthly_limit_reach': monthly_limit_reach_global, # Agency wide limit status
                    'remaining_links_to_removal': remaining_links_to_removal, # Shared pool remaining
                    'name': name,
                    'avatar': avatar
                }
                
                return success(data=items, message='Dashboard data fetched successfully.')

            except AgencyMemberList.DoesNotExist:
                return error(message='Agency member not found')

        else:
            return error(message='Invalid user role')