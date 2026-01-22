from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from apps.customer_support.models import Message, Reply
from apps.user.models import User
from rest_framework.views import APIView
from .serializers import GetMessageSerializer
from django.db.models import Q, Prefetch

from apps.utils.helpers import success, error

# Create your views here.
class SendMessageView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        admin = User.objects.get(id=1)
        txt = request.data.get('txt')
        print(txt)
        message = Message.objects.create(
            sender=user,
            recipient=admin,
            txt=txt
        )
        return success(data={"message_id": message.id}, message="Message sent successfully")



class GetMessagesView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        # Get messages where user is either sender or recipient
        messages = Message.objects.filter(
            Q(sender=user) | Q(recipient=user)
        ).select_related('sender', 'recipient').prefetch_related(
            Prefetch('replies', queryset=Reply.objects.select_related('responder'))
        ).order_by('sent_at')
        
        if not messages.exists():
            return error(message="No messages found.", errors=None, code=200)

        get_message = GetMessageSerializer(messages, many=True)

        return success(data=get_message.data)
        