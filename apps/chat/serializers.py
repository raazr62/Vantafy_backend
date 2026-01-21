from rest_framework import serializers
from apps.user.models import User
from .models import ChatRoom, Message, MessageReaction
from django.db.models import Q
from django.core.cache import cache


class MyChatListUserSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()
    unread_message_count = serializers.SerializerMethodField()
    unread_message_ids = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'full_name', 'avatar', 'last_message', 'is_online', 'unread_message_count', 'unread_message_ids']

class MessageReactionSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.name', read_only=True)
    
    class Meta:
        model = MessageReaction
        fields = ['id', 'user', 'user_name', 'emoji', 'created_at']

class MessageSerializer(serializers.ModelSerializer):
    reactions = MessageReactionSerializer(many=True, read_only=True)
    parent_message = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'receiver', 'content', 'file', 'file_url', 'message_type', 'timestamp', 'is_read', 'parent_message', 'reactions']
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
        
    def get_parent_message(self, obj):
        if obj.parent_message:
            return MessageSerializer(obj.parent_message).data
        return None




    def get_last_message(self, obj):
        last_message = Message.objects.filter(Q(sender=obj) | Q(receiver=obj)).order_by('-timestamp').first()
        return last_message.content if last_message else None

    def get_is_online(self, obj):
        """
        Check if user is online by checking the cache
        Users are marked as online when they connect to WebSocket
        and marked as offline when they disconnect
        """
        try:
            # Get online users from cache
            online_users = cache.get('online_users', set())
            return obj.id in online_users
        except Exception as e:
            # If cache fails, return False
            print(f"Error checking online status for user {obj.id}: {e}")
            return False
    

    def get_unread_message_count(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            room_name = f"chat_{min(request.user.id, obj.id)}_{max(request.user.id, obj.id)}"
            try:
                room = ChatRoom.objects.get(name=room_name)
                return Message.objects.filter(room=room, sender=obj, receiver=request.user, is_read=False).count()
            except ChatRoom.DoesNotExist:
                return 0
        return 0
    

    def get_unread_message_ids(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            room_name = f"chat_{min(request.user.id, obj.id)}_{max(request.user.id, obj.id)}"
            try:
                room = ChatRoom.objects.get(name=room_name)
                unread_messages = Message.objects.filter(room=room, sender=obj, receiver=request.user, is_read=False)
                return list(unread_messages.values_list('id', flat=True))
            except ChatRoom.DoesNotExist:
                return []
        return []

    
    
