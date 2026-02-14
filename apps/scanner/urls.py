from django.urls import path

from .views import (
    SpiderListView,
    ScanNowView,
    ScanRunTimeResultView,
    ScanResultListView,
    LinkRemovalRequestAPIView,
    # DashboardDataAPIView,
  
)

urlpatterns = [
    # Spiders
    path("spiders-list/", SpiderListView.as_view(), name="spider_list"),
    
    # Scan operations
    path("scan-now/", ScanNowView.as_view(), name="scan_now"),
    path("scan-run-time-result/", ScanRunTimeResultView.as_view(), name="scan_run_time_result"),
    path("scan-results/", ScanResultListView.as_view(), name="scan_result_list"),

    # link request for removal
    path("link-removal-request/", LinkRemovalRequestAPIView.as_view(), name="link_removal_request"),

    #Dashboard data
    # path("dashboard-data/", DashboardDataAPIView.as_view(), name="user_dashboard_data")

    ]
