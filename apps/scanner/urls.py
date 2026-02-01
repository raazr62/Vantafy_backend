from django.urls import path

from .views import (
    SpiderListView,
    ScanNowView,
    ScanResultListView,
    ScanResultDetailsView,
  
)

urlpatterns = [
    # Spiders
    path("spiders-list/", SpiderListView.as_view(), name="spider_list"),
    
    # Scan operations
    path("scan-now/", ScanNowView.as_view(), name="scan_now"),
    path("scan-results/", ScanResultListView.as_view(), name="scan_result_list"),
    path('scan-result-details/<int:scan_result_id>/', ScanResultDetailsView.as_view(), name='scan_result_details'),
]
