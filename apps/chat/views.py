from django.shortcuts import render
from django.db.models import Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from apps.user.authentication import CookieJWTAuthentication
from apps.user.models import User
from apps.utils.helpers import success, error
from .models import ChatRoom, Message, MessageReaction
from .serializers import  MessageSerializer, MyChatListUserSerializer


class MyChatListUserAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]
    
    def get(self, request):
    
        my_chat_list_users = User.objects.filter(
            Q(sent_message__receiver=request.user) | Q(received_message__sender=request.user)
        ).distinct()

        print("My chat list users:", my_chat_list_users)
        
        serializer = MyChatListUserSerializer(my_chat_list_users, many=True, context={'request': request})
        return success(data=serializer.data, message="My chat list users retrieved successfully")


class GetSingleUserAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            serializer = MyChatListUserSerializer(user, context={'request': request})

            data = serializer.data
                
            return success(data=data, message="User details retrieved successfully")
        except User.DoesNotExist:
            return error(message='User not found', code=status.HTTP_404_NOT_FOUND)
        

class SearchUserAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def get(self, request):
        query = request.GET.get('name', '')

        users = User.objects.filter(
            Q(full_name__icontains=query) | Q(email__icontains=query)
        ).exclude(id=request.user.id)
        
        serializer = MyChatListUserSerializer(users, many=True, context={'request': request})

        return success(data=serializer.data, message="User search results retrieved successfully")




class GetMessageAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def get(self, request, user_id):
        try:
            other_user = User.objects.get(id=user_id)
            if not other_user:
                return error(message='User not found', code=status.HTTP_404_NOT_FOUND)
            
            room_name = f"chat_{min(request.user.id, other_user.id)}_{max(request.user.id, other_user.id)}"
            chat_room, created = ChatRoom.objects.get_or_create(name=room_name)
            
            if created:
                chat_room.participants.add(request.user, other_user)
            
            messages = Message.objects.filter(
                room=chat_room
            ).select_related('sender', 'receiver',).order_by('timestamp')  
            
            serializer = MessageSerializer(messages, many=True, context={'request': request})
            return success(data=serializer.data, message="Chat history retrieved successfully")
        except User.DoesNotExist:
            return error(message='User not found', code=status.HTTP_404_NOT_FOUND)


class MarkReadAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def post(self, request):
        message_ids = request.data.get('message_ids', [])
        if not message_ids:
            return error(message='No message IDs provided', code=status.HTTP_400_BAD_REQUEST)
        
        updated_count = Message.objects.filter(
            id__in=message_ids,
            receiver=request.user
        ).update(is_read=True)
        
        return success(data={'updated_count': updated_count}, message=f'{updated_count} message(s) marked as read')
    







class AllUnreadNewMessagesCountAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def get(self, request):
        unread_count = Message.objects.filter(
            receiver=request.user,
            is_read=False
        ).count()
        
        return success(data={'unread_count': unread_count}, message="Total unread messages count retrieved successfully")

class AddReactionAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def post(self, request):
        message_id = request.data.get('message_id')
        emoji = request.data.get('emoji')

        if not message_id or not emoji:
            return error(message='Message ID and Emoji are required', code=status.HTTP_400_BAD_REQUEST)

        try:
            message = Message.objects.get(id=message_id)
            # Create or delete reaction (toggle)? For now let's just create/update
            # Actually, standard behavior is usually toggle or just add. 
            # Simple implementation: Create if not exists, nothing if exists.
            # Or unique_together will raise error.
            
            reaction, created = MessageReaction.objects.get_or_create(
                message=message,
                user=request.user,
                defaults={'emoji': emoji}
            )
            
            if not created:
                # Update emoji if different
                if reaction.emoji != emoji:
                    reaction.emoji = emoji
                    reaction.save()
                else:
                    # Toggle off if same emoji? Let's just keep it simple: set reaction.
                    pass
            
            # Broadcast reaction via WebSocket
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            
            channel_layer = get_channel_layer()
            # Get the room name for this message
            room_group_name = f'chat_{min(message.sender.id, message.receiver.id)}_{max(message.sender.id, message.receiver.id)}'
            
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'message_reaction',
                    'message_id': message.id,
                    'user_id': request.user.id,
                    'user_name': request.user.full_name,
                    'emoji': emoji,
                    'action': 'added'
                }
            )
            
            return success(data=reaction.emoji, message="Reaction added successfully")

        except Message.DoesNotExist:
            return error(message='Message not found', code=status.HTTP_404_NOT_FOUND)


class SendFileMessageAPIView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [CookieJWTAuthentication]

    def post(self, request):
        receiver_id = request.data.get('receiver_id')
        file = request.FILES.get('file')
        caption = request.data.get('caption', '')

        if not receiver_id:
            return error(message='Receiver ID is required', code=status.HTTP_400_BAD_REQUEST)
        
        if not file:
            return error(message='File is required', code=status.HTTP_400_BAD_REQUEST)

        try:
            receiver = User.objects.get(id=receiver_id)
            
            # Detect file type based on mime type
            content_type = file.content_type
            if content_type.startswith('image/'):
                file_type = 'image'
            elif content_type.startswith('video/'):
                file_type = 'video'
            elif content_type.startswith('audio/'):
                file_type = 'audio'
            elif content_type in ['application/pdf', 'application/msword', 
                                   'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                                   'application/vnd.ms-excel',
                                   'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                                   'text/plain']:
                file_type = 'document'
            else:
                file_type = 'file'
            
            # Get or create chat room
            room_name = f'chat_{min(request.user.id, receiver.id)}_{max(request.user.id, receiver.id)}'
            room, created = ChatRoom.objects.get_or_create(name=room_name)
            
            if created:
                room.participants.add(request.user, receiver)
            
            # Create message with file
            message = Message.objects.create(
                room=room,
                sender=request.user,
                receiver=receiver,
                content=caption,
                file=file,
                message_type=file_type
            )
            
            serializer = MessageSerializer(message, context={'request': request})
            
            # Broadcast via WebSocket
            from channels.layers import get_channel_layer
            from asgiref.sync import async_to_sync
            
            channel_layer = get_channel_layer()
            room_group_name = f'chat_{min(request.user.id, receiver.id)}_{max(request.user.id, receiver.id)}'
            
            async_to_sync(channel_layer.group_send)(
                room_group_name,
                {
                    'type': 'chat_message',
                    'message': caption,
                    'sender_id': request.user.id,
                    'receiver_id': receiver.id,
                    'timestamp': message.timestamp.isoformat(),
                    'message_id': message.id,
                    'message_type': file_type,
                    'file_url': request.build_absolute_uri(message.file.url) if message.file else None
                }
            )
            
            return success(data=serializer.data, message='File message sent successfully')
            
        except User.DoesNotExist:
            return error(message='Receiver not found', code=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return error(message=str(e), code=status.HTTP_500_INTERNAL_SERVER_ERROR)
