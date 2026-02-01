from django.urls import path

from .views import (
    SpiderListView,
    ScanNowView,
  
)

urlpatterns = [
    # Spiders
    path("spiders-list/", SpiderListView.as_view(), name="spider_list"),
    
    # Scan operations
    path("scan-now/", ScanNowView.as_view(), name="scan_now"),
   
]
