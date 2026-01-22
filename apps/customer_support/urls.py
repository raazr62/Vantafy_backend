from django.urls import path

from .views import SendMessageView,GetMessagesView



urlpatterns = [
    path('send-message/', SendMessageView.as_view()),
    path('get-messages/', GetMessagesView.as_view()),
]