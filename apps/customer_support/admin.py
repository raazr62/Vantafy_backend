# admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.shortcuts import render, redirect
from django.contrib import messages as django_messages
from django.db import models
from unfold.admin import ModelAdmin
from unfold.decorators import display

from .models import Message, Reply

@admin.register(Message)
class MessageAdmin(ModelAdmin):
    list_display = [
        'message_preview', 
        'sender_info', 
        'recipient_info', 
        'sent_at_formatted',
        'attachments_indicator',
        'status_badges',
        'reply_count',
        'message_actions'
    ]
    list_filter = ['is_read', 'sent_at', 'sender', 'recipient']
    search_fields = ['txt', 'sender__email', 'recipient__email']
    readonly_fields = ['sent_at']
    ordering = ['-sent_at']
    actions = ['mark_as_read_action', 'mark_as_unread_action']
    
    fieldsets = (
        (None, {
            'fields': ('sender', 'recipient', 'txt', 'sent_at', 'is_read')
        }),
        ('Attachments', {
            'fields': ('image', 'file', 'document'),
            'classes': ('collapse',)
        }),
    )

    @display(description="Message", ordering="txt")
    def message_preview(self, obj):
        preview = obj.txt[:50] + "..." if len(obj.txt) > 50 else obj.txt
        return format_html('<strong>{}</strong>', preview)

    @display(description="Sender")
    def sender_info(self, obj):
        url = reverse("admin:user_user_change", args=[obj.sender.id])
        return format_html('<a href="{}">{}</a>', url, obj.sender.email)

    @display(description="Recipient")
    def recipient_info(self, obj):
        url = reverse("admin:user_user_change", args=[obj.recipient.id])
        return format_html('<a href="{}">{}</a>', url, obj.recipient.email)

    @display(description="Sent At", ordering="sent_at")
    def sent_at_formatted(self, obj):
        return obj.sent_at.strftime("%Y-%m-%d %H:%M")
    
    @display(description="Attachments")
    def attachments_indicator(self, obj):
        """Show icons for attachments"""
        icons = []
        if obj.image:
            icons.append('<span style="color: #3498db;" title="Has Image">🖼️</span>')
        if obj.file:
            icons.append('<span style="color: #9b59b6;" title="Has File">📎</span>')
        if obj.document:
            icons.append('<span style="color: #e67e22;" title="Has Document">📄</span>')
        return format_html(' '.join(icons)) if icons else format_html('<span style="color: #bdc3c7;">—</span>')

    @display(description="Status")
    def status_badges(self, obj):
        """Show status badges for admin read/unread and new messages"""
        badges = []
        
        # Check if message is new (less than 24 hours old)
        from django.utils import timezone
        from datetime import timedelta
        is_new = (timezone.now() - obj.sent_at) < timedelta(hours=24)
        
        # Admin read/unread status (most important)
        if not obj.is_read:
            badges.append('<span style="background: #e74c3c; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; margin-right: 4px; display: inline-block; font-weight: bold;">📬 UNREAD</span>')
        else:
            badges.append('<span style="background: #2ecc71; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; margin-right: 4px; display: inline-block;">✅ Read</span>')
        
        # New message badge
        if is_new:
            badges.append('<span style="background: #3498db; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; margin-right: 4px; display: inline-block;">🆕 NEW</span>')
        
        # Reply status
        reply_count = obj.replies.count()
        if reply_count > 0:
            badges.append(f'<span style="background: #27ae60; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; margin-right: 4px; display: inline-block;">💬 {reply_count} Replied</span>')
        else:
            badges.append('<span style="background: #f39c12; color: white; padding: 3px 8px; border-radius: 12px; font-size: 11px; margin-right: 4px; display: inline-block;">⏳ No Reply</span>')
        
        return format_html(''.join(badges))

    @display(description="Replies")
    def reply_count(self, obj):
        count = obj.replies.count()
        if count > 0:
            return format_html(
                '<span style="color: #2ecc71; font-weight: bold;">{}</span>',
                count
            )
        else:
            return format_html(
                '<span style="color: #95a5a6;">0</span>'
            )


    @display(description="Actions")
    def message_actions(self, obj):
        reply_url = reverse("admin:customer_support_message_reply", args=[obj.id])
        view_url = reverse("admin:customer_support_message_change", args=[obj.id])
        
        return format_html(
            '<a href="{}" class="button" style="background: #007cba; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px; margin-right: 5px;">Reply</a>'
            '<a href="{}" class="button" style="background: #6c757d; color: white; padding: 5px 10px; text-decoration: none; border-radius: 3px;">View</a>',
            reply_url, view_url
        )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # For non-superusers, show only their messages
        if not request.user.is_superuser:
            qs = qs.filter(models.Q(sender=request.user) | models.Q(recipient=request.user))
        return qs

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                '<path:object_id>/reply/',
                self.admin_site.admin_view(self.reply_view),
                name='customer_support_message_reply',
            ),
        ]
        return custom_urls + urls

    def reply_view(self, request, object_id):
        message = self.get_object(request, object_id)
        
        if request.method == 'POST':
            reply_text = request.POST.get('reply_text')
            if reply_text:
                Reply.objects.create(
                    message=message,
                    responder=request.user,
                    reply_txt=reply_text
                )
                django_messages.success(request, 'Reply sent successfully!')
                return redirect('admin:customer_support_message_changelist')
        
        # Mark message as read when admin views it
        if not message.is_read:
            message.is_read = True
            message.save()
        
        # Get all replies for this message
        replies = message.replies.all().order_by('replied_at')
        
        context = {
            'message': message,
            'replies': replies,
            'title': f'Reply to {message.sender.email}',
            'opts': self.model._meta,
            **self.admin_site.each_context(request),
        }
        
        return render(request, 'admin/messaging/message_reply.html', context)
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Mark message as read when admin views it"""
        obj = self.get_object(request, object_id)
        if obj and not obj.is_read:
            obj.is_read = True
            obj.save()
        return super().change_view(request, object_id, form_url, extra_context)
    
    def mark_as_read_action(self, request, queryset):
        """Bulk action to mark messages as read"""
        updated = queryset.update(is_read=True)
        self.message_user(request, f'{updated} message(s) marked as read.')
    mark_as_read_action.short_description = "Mark selected messages as read"
    
    def mark_as_unread_action(self, request, queryset):
        """Bulk action to mark messages as unread"""
        updated = queryset.update(is_read=False)
        self.message_user(request, f'{updated} message(s) marked as unread.')
    mark_as_unread_action.short_description = "Mark selected messages as unread"

@admin.register(Reply)
class ReplyAdmin(ModelAdmin):
    list_display = [
        'reply_preview',
        'message_link',
        'responder_info',
        'replied_at_formatted',
    ]
    list_filter = ['replied_at', 'responder']
    search_fields = ['reply_txt', 'message__txt', 'responder__email']
    readonly_fields = ['replied_at']
    ordering = ['-replied_at']
    actions = ['mark_as_read']

    @display(description="Reply")
    def reply_preview(self, obj):
        preview = obj.reply_txt[:50] + "..." if len(obj.reply_txt) > 50 else obj.reply_txt
        return format_html('<strong>{}</strong>', preview)

    @display(description="Message")
    def message_link(self, obj):
        url = reverse("admin:customer_support_message_change", args=[obj.message.id])
        preview = obj.message.txt[:30] + "..." if len(obj.message.txt) > 30 else obj.message.txt
        return format_html('<a href="{}">{}</a>', url, preview)

    @display(description="Responder")
    def responder_info(self, obj):
        url = reverse("admin:user_user_change", args=[obj.responder.id])
        return format_html('<a href="{}">{}</a>', url, obj.responder.email)

    @display(description="Replied At", ordering="replied_at")
    def replied_at_formatted(self, obj):
        return obj.replied_at.strftime("%Y-%m-%d %H:%M")

  
