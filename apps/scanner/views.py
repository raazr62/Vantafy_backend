from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from .models import ScanJob, ScanResult
from .serializers import (
    ScanJobListSerializer,
    ScanJobDetailSerializer,
    CreateScanSerializer,
    ScanResultSerializer,
)
from .services import get_available_spiders, run_all_spiders_async


class SpiderListView(APIView):
    """
    GET: List all available spiders.
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        spiders = get_available_spiders()
        return Response({
            'count': len(spiders),
            'spiders': spiders
        })


class ScanNowView(APIView):

    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = CreateScanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        creator_name = serializer.validated_data['creator_name']
        
        # Get available spiders
        spiders = get_available_spiders()
        
        if not spiders:
            return Response(
                {'error': 'No spiders available. Check spider configuration.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Create scan job
        scan_job = ScanJob.objects.create(
            creator_name=creator_name,
            user=request.user if request.user.is_authenticated else None,
            total_spiders=len(spiders),
            status='pending'
        )
        
        # Start background scanning
        run_all_spiders_async(creator_name, scan_job.id, spiders)
        
        return Response({
            'message': 'Scan started successfully',
            'job': ScanJobListSerializer(scan_job).data
        }, status=status.HTTP_201_CREATED)
    
    def get(self, request):
        """For backwards compatibility - redirect to POST info."""
        return Response({
            'message': 'Use POST to start a scan',
            'required_fields': {
                'creator_name': 'Name of the creator to search for'
            }
        })


class ScanJobListView(ListAPIView):
    """
    GET: List all scan jobs (paginated).
    """
    permission_classes = [AllowAny]
    serializer_class = ScanJobListSerializer
    queryset = ScanJob.objects.all()
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by status if provided
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by user if authenticated
        if self.request.user.is_authenticated:
            user_only = self.request.query_params.get('my_jobs', 'false').lower() == 'true'
            if user_only:
                queryset = queryset.filter(user=self.request.user)
        
        return queryset


class ScanJobDetailView(RetrieveAPIView):
    """
    GET: Get scan job details with all results.
    """
    permission_classes = [AllowAny]
    serializer_class = ScanJobDetailSerializer
    queryset = ScanJob.objects.prefetch_related('results')
    lookup_field = 'pk'


class ScanJobStatusView(APIView):
    """
    GET: Get real-time status of a scan job.
    """
    permission_classes = [AllowAny]
    
    def get(self, request, pk):
        try:
            scan_job = ScanJob.objects.get(pk=pk)
        except ScanJob.DoesNotExist:
            return Response(
                {'error': 'Scan job not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({
            'id': str(scan_job.id),
            'status': scan_job.status,
            'progress': {
                'completed': scan_job.completed_spiders,
                'total': scan_job.total_spiders,
                'percentage': scan_job.progress_percentage
            },
            'results_summary': {
                'total_images': scan_job.total_images,
                'total_videos': scan_job.total_videos,
                'websites_with_results': scan_job.results.exclude(images=[], videos=[]).count()
            }
        })


class ScanJobCancelView(APIView):
    """
    POST: Cancel a running scan job.
    """
    permission_classes = [AllowAny]
    
    def post(self, request, pk):
        try:
            scan_job = ScanJob.objects.get(pk=pk)
        except ScanJob.DoesNotExist:
            return Response(
                {'error': 'Scan job not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if scan_job.status not in ['pending', 'running']:
            return Response(
                {'error': f'Cannot cancel job with status: {scan_job.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        scan_job.status = 'cancelled'
        scan_job.save()
        
        return Response({
            'message': 'Scan job cancelled',
            'job': ScanJobListSerializer(scan_job).data
        })


class ScanResultsView(ListAPIView):
    """
    GET: Get all results for a specific scan job.
    Query params:
    - has_content: true/false - filter results with/without content
    """
    permission_classes = [AllowAny]
    serializer_class = ScanResultSerializer
    
    def get_queryset(self):
        job_id = self.kwargs.get('pk')
        queryset = ScanResult.objects.filter(scan_job_id=job_id)
        
        # Filter by content
        has_content = self.request.query_params.get('has_content')
        if has_content == 'true':
            queryset = queryset.exclude(images=[], videos=[])
        elif has_content == 'false':
            queryset = queryset.filter(images=[], videos=[])
        
        return queryset