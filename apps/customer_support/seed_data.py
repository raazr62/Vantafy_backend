from apps.customer_support.models import Message, Reply
from django.contrib.auth import get_user_model
import random
from apps.user.models import User

def seed_messages():
    if Message.objects.exists():
        print("[INFO] Customer support messages already seeded.")
        return

    sender = User.objects.filter(id=2).first()
    recipient = User.objects.filter(id=1).first()
    
    if not sender or not recipient:
        print("[ERROR] Cannot seed messages: Users with id 1 and 2 not found.")
        return

    messages_data = [
        "Hello, I need help with my order.",
        "Can you provide more information about your services?",
        "I have a question regarding my account.",
        "Thank you for your assistance!",
        "Is there a way to track my shipment?",
    ]
    
    for _ in range(5):  # Seed 5 messages
        message_text = random.choice(messages_data)
        
        Message.objects.create(
            sender=sender,
            recipient=recipient,
            txt=message_text
        )
    print("[SUCCESS] Seeded 5 messages.")

def seed_replies():
    if Reply.objects.exists():
        print("[INFO] Message replies already seeded.")
        return
    replies_data = [
        "Thank you for reaching out. How can I assist you?",
        "We are looking into your issue and will get back to you shortly.",
        "Please provide more details about your concern.",
        "Your satisfaction is our priority. Let us know how we can help.",
        "We appreciate your feedback!",
    ]
    
    responder = User.objects.filter(id=1).first()
    if not responder:
        print("[ERROR] Cannot seed replies: User with id 1 not found.")
        return
    
    messages = Message.objects.all()
    for message in messages:
        reply_text = random.choice(replies_data)
        
        Reply.objects.create(
            message=message,
            responder=responder,
            reply_txt=reply_text
        )
    print("[SUCCESS] Seeded replies for messages.")