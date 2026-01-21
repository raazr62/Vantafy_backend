# admin.py
from django.contrib import admin
from django.utils.html import format_html
from unfold.admin import ModelAdmin
from unfold.decorators import display
from .models import ChatRoom, Message

@admin.register(ChatRoom)
class ChatRoomAdmin(ModelAdmin):
    list_display = ['name', 'participant_count', 'created_at']
    search_fields = ['name']
    filter_horizontal = ['participants']
    readonly_fields = ['created_at']
    
    @display(description="Participants")
    def participant_count(self, obj):
        count = obj.participants.count()
        return format_html('<span style="font-weight: bold;">{}</span>', count)

@admin.register(Message)
class MessageAdmin(ModelAdmin):
    list_display = ['message_preview', 'sender_email', 'receiver_email', 'timestamp', 'read_status']
    list_filter = ['is_read', 'timestamp']
    search_fields = ['content', 'sender__email', 'receiver__email']
    readonly_fields = ['timestamp']
    raw_id_fields = ['sender', 'receiver', 'room']
    
    @display(description="Message", ordering="content")
    def message_preview(self, obj):
        preview = obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
        return format_html('<span style="color: #333;">{}</span>', preview)
    
    @display(description="From")
    def sender_email(self, obj):
        return obj.sender.email
    
    @display(description="To")
    def receiver_email(self, obj):
        return obj.receiver.email
    
    @display(description="Status")
    def read_status(self, obj):
        if obj.is_read:
            return format_html(
                '<span style="background: #2ecc71; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">✓ Read</span>'
            )
        else:
            return format_html(
                '<span style="background: #e74c3c; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px;">● Unread</span>'
            )