# models.py
from django.db import models
from apps.user.models import User

class Message(models.Model):
    sender = models.ForeignKey(User, related_name='sent_messages', on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, related_name='received_messages', on_delete=models.CASCADE)
    txt = models.TextField()
    image = models.ImageField(upload_to='customer_support/messages/', null=True, blank=True)
    file = models.FileField(upload_to='customer_support/files/', null=True, blank=True)
    document = models.FileField(upload_to='customer_support/documents/', null=True, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"Message from {self.sender} to {self.recipient}"

    def get_reply_count(self):
        return self.replies.count()

class Reply(models.Model):
    message = models.ForeignKey(Message, related_name='replies', on_delete=models.CASCADE)
    responder = models.ForeignKey(User, related_name='replies', on_delete=models.CASCADE)
    reply_txt = models.TextField()
    replied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['replied_at']

    def __str__(self):
        return f"Reply by {self.responder}"