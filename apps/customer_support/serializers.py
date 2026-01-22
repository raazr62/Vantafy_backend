from .models import Message, Reply
from apps.user.models import User
from rest_framework import serializers


class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for messages"""
    
    class Meta:
        model = User
        fields = ['id', 'email']


class ReplySerializer(serializers.ModelSerializer):
    """Serializer for Reply model"""
    responder = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = Reply
        fields = ['id', 'responder', 'reply_txt', 'replied_at']


class MessageSerializer(serializers.ModelSerializer):
    """Basic message serializer"""
    sender = UserBasicSerializer(read_only=True)
    recipient = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'recipient', 'txt', 'sent_at']


class GetMessageSerializer(serializers.ModelSerializer):
    """Serializer for getting messages with replies"""
    sender = UserBasicSerializer(read_only=True)
    recipient = UserBasicSerializer(read_only=True)
    replies = ReplySerializer(many=True, read_only=True)
    reply_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'recipient', 'txt', 'sent_at', 'replies', 'reply_count']
    
    def get_reply_count(self, obj):
        return obj.replies.count()