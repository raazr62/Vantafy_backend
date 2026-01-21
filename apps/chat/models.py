from django.db import models
from apps.user.models import User

class ChatRoom(models.Model):
    name = models.CharField(max_length=255, unique=True)
    participants = models.ManyToManyField(User)
    created_at = models.DateTimeField(auto_now_add=True)

class Message(models.Model):

    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE)
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_message')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_message')
    content = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='chat_files/', blank=True, null=True)
    message_type = models.CharField(
        max_length=20, 
        choices=[
            ('text', 'Text'),
            ('image', 'Image'),
            ('video', 'Video'),
            ('audio', 'Audio'),
            ('document', 'Document'),
            ('file', 'File')
        ], 
        default='text'
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    parent_message = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='replies')

    class Meta:
        ordering = ['timestamp']

class MessageReaction(models.Model):
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='reactions')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    emoji = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('message', 'user', 'emoji')
