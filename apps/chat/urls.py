from django.urls import path
from .views import MyChatListUserAPIView,SearchUserAPIView,GetMessageAPIView,MarkReadAPIView, GetSingleUserAPIView , AllUnreadNewMessagesCountAPIView, AddReactionAPIView, SendFileMessageAPIView


urlpatterns = [
    path('my-chat-list-users/', MyChatListUserAPIView.as_view()),
    path("get-single-user/<int:user_id>/", GetSingleUserAPIView.as_view()),
    path('search-users/', SearchUserAPIView.as_view()),
    path('messages/<int:user_id>/', GetMessageAPIView.as_view()),
    path('messages-mark-read/', MarkReadAPIView.as_view(), name='mark_read'),
    path('messages-reaction/', AddReactionAPIView.as_view(), name='add_reaction'),
    path('messages-send-file/', SendFileMessageAPIView.as_view(), name='send_file'),
    path("all-unread-new-messages-count/", AllUnreadNewMessagesCountAPIView.as_view()),
]