from django.urls import path

from .views import (
    SpiderListView,
    ScanNowView,
    ScanJobListView,
    ScanJobDetailView,
    ScanJobStatusView,
    ScanJobCancelView,
    ScanResultsView,
)

urlpatterns = [
    # Spiders
    path("spiders-list/", SpiderListView.as_view(), name="spider_list"),
    
    # Scan operations
    path("scan-now/", ScanNowView.as_view(), name="scan_now"),
    path("scan-jobs-list/", ScanJobListView.as_view(), name="scan_job_list"),
    path("scan/jobs/<uuid:pk>/", ScanJobDetailView.as_view(), name="scan_job_detail"),
    path("scan/jobs/<uuid:pk>/status/", ScanJobStatusView.as_view(), name="scan_job_status"),
    path("scan/jobs/<uuid:pk>/cancel/", ScanJobCancelView.as_view(), name="scan_job_cancel"),
    path("scan/jobs/<uuid:pk>/results/", ScanResultsView.as_view(), name="scan_job_results"),
]
