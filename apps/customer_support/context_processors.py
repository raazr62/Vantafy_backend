# apps/customer_support/context_processors.py
from django.db.models import Q
from apps.customer_support.models import Reply, Message
from django.utils import timezone
from datetime import timedelta


def messaging_stats(request):
    """
    Context processor to add messaging statistics to all templates
    For admin users, tracks unread messages (admin hasn't read them yet)
    For regular users, tracks unread replies
    """
    if request.user.is_authenticated:
        stats = {
            'recent_messages': Message.objects.filter(
                Q(sender=request.user) | Q(recipient=request.user)
            ).order_by('-sent_at')[:3]
        }
        
        # For admin users, count unread messages (messages admin hasn't read)
        if request.user.is_staff:
            stats['unread_count'] = Message.objects.filter(is_read=False).count()
            stats['new_messages_24h'] = Message.objects.filter(
                sent_at__gte=timezone.now() - timedelta(hours=24)
            ).count()
            stats['unreplied_messages'] = Message.objects.filter(
                replies__isnull=True
            ).distinct().count()
        else:
            # For regular users, count unread replies
            stats['unread_count'] = Reply.objects.filter(
                message__sender=request.user,
                is_read=False
            ).count()
        
        return stats
        
    return {
        'unread_count': 0,
        'recent_messages': [],
        'new_messages_24h': 0,
        'unreplied_messages': 0
    }