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
    image_url = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    document_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'recipient', 'txt', 'image', 'file', 'document', 'image_url', 'file_url', 'document_url', 'sent_at']
    
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def get_document_url(self, obj):
        if obj.document:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.document.url)
            return obj.document.url
        return None


class GetMessageSerializer(serializers.ModelSerializer):
    """Serializer for getting messages with replies"""
    sender = UserBasicSerializer(read_only=True)
    recipient = UserBasicSerializer(read_only=True)
    replies = ReplySerializer(many=True, read_only=True)
    reply_count = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    document_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Message
        fields = ['id', 'sender', 'recipient', 'txt', 'image', 'file', 'document', 'image_url', 'file_url', 'document_url', 'sent_at', 'replies', 'reply_count']
    
    def get_reply_count(self, obj):
        return obj.replies.count()
    
    def get_image_url(self, obj):
        if obj.image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.image.url)
            return obj.image.url
        return None
    
    def get_file_url(self, obj):
        if obj.file:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.file.url)
            return obj.file.url
        return None
    
    def get_document_url(self, obj):
        if obj.document:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.document.url)
            return obj.document.url
        return None