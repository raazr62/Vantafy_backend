from django.urls import path
from .views import LandingPageAllSectionOneByOneView, PageView

urlpatterns = [
    path('landing-page-all-section-one-by-one/',LandingPageAllSectionOneByOneView.as_view(), name='landing-page-all-section-one-by-one'),
    path('pages/',PageView.as_view(), name='page'),
]
