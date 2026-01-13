from django.urls import path
from .views import LandingPageAllSectionOneByOneView

urlpatterns = [
    path('landing-page-all-section-one-by-one/',LandingPageAllSectionOneByOneView.as_view(), name='landing-page-all-section-one-by-one'),
]
