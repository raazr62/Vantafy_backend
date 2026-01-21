import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.core.cache import cache
from apps.user.models import User
from .models import Message, ChatRoom, MessageReaction

class PrivateChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        print("WebSocket connection initiated.")
        self.sender_id = int(self.scope['url_route']['kwargs']['sender_id'])
        self.receiver_id = int(self.scope['url_route']['kwargs']['receiver_id'])

        # Create a consistent room name regardless of sender/receiver order
        self.room_group_name = f'chat_{min(self.sender_id, self.receiver_id)}_{max(self.sender_id, self.receiver_id)}'

        # Mark user as online
        await self.set_user_online(self.sender_id)

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        # Mark user as offline
        await self.set_user_offline(self.sender_id)

        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        try:
            # Check if text_data is empty or whitespace
            if not text_data or not text_data.strip():
                print("Received empty message, ignoring...")
                return
            
            # Try to parse as JSON first, if it fails, treat as plain text
            try:
                text_data_json = json.loads(text_data)
                is_json = True
            except json.JSONDecodeError:
                is_json = False
                message = text_data.strip()
                print(f"Received plain text: {message}")
            
            if is_json:
                msg_type = text_data_json.get('type', 'chat_message')
                message = text_data_json.get('message', '').strip()
            else:
                msg_type = 'chat_message'
                # message already set
            
            if msg_type == 'typing_start' or msg_type == 'typing_stop':
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'user_typing',
                        'user_id': self.sender_id,
                        'is_typing': (msg_type == 'typing_start')
                    }
                )
                return

            if msg_type == 'chat_message':
                # message is already set above
                # Validate message content
                if not message:
                    await self.send(text_data=json.dumps({
                        'error': 'Message content cannot be empty',
                        'status': 'error'
                    }))
                    return
                
                # Save message to database
                saved_message = await self.save_message(
                    sender_id=self.sender_id,
                    receiver_id=self.receiver_id,
                    content=message
                )
                
                # Refresh online status (extend timeout)
                await self.set_user_online(self.sender_id)
                
                # Send message to room group
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message,
                        'sender_id': self.sender_id,
                        'receiver_id': self.receiver_id,
                        'timestamp': saved_message['timestamp'],
                        'message_id': saved_message['id']
                    }
                )
        except Exception as e:
            print(f"Error in receive: {e}")
            import traceback
            traceback.print_exc()
            await self.send(text_data=json.dumps({
                'error': str(e),
                'status': 'error'
            }))

    async def chat_message(self, event):
        print(event)
        # Send message to WebSocket
        message_data = {
            'message': event['message'],
            'sender_id': int(event['sender_id']),
            'receiver_id': int(event['receiver_id']),
            'timestamp': event['timestamp'],
            'message_id': int(event['message_id']),
            'message_type': event.get('message_type', 'text')
        }
        
        # Add file_url if present
        if event.get('file_url'):
            message_data['file_url'] = event['file_url']
        
        await self.send(text_data=json.dumps(message_data))

    async def user_typing(self, event):
        await self.send(text_data=json.dumps({
            'type': 'user_typing',
            'user_id': event['user_id'],
            'is_typing': event['is_typing']
        }))
    
    async def message_reaction(self, event):
        """Handle message reaction events"""
        await self.send(text_data=json.dumps({
            'type': 'message_reaction',
            'message_id': event['message_id'],
            'user_id': event['user_id'],
            'user_name': event['user_name'],
            'emoji': event['emoji'],
            'action': event['action']
        }))
    
    @database_sync_to_async
    def save_message(self, sender_id, receiver_id, content):
        try:
            sender = User.objects.get(id=sender_id)
            receiver = User.objects.get(id=receiver_id)
            
            # Get or create chat room
            room_name = f'chat_{min(sender_id, receiver_id)}_{max(sender_id, receiver_id)}'
            room, created = ChatRoom.objects.get_or_create(name=room_name)
            
            if created:
                room.participants.add(sender, receiver)
            
            # Create message
            message = Message.objects.create(
                room=room,
                sender=sender,
                receiver=receiver,
                content=content
            )
            
            return {
                'id': message.id,
                'timestamp': message.timestamp.isoformat()
            }
        except Exception as e:
            print(f"Error saving message: {e}")
            raise

    @database_sync_to_async
    def set_user_online(self, user_id):
        """Mark user as online in cache"""
        try:
            # Get current online users
            online_users = cache.get('online_users', set())
            online_users.add(user_id)
            # Set cache with 5 minute timeout (will be refreshed on activity)
            cache.set('online_users', online_users, 300)
            print(f"User {user_id} marked as online")
        except Exception as e:
            print(f"Error setting user online: {e}")

    @database_sync_to_async
    def set_user_offline(self, user_id):
        """Mark user as offline in cache"""
        try:
            # Get current online users
            online_users = cache.get('online_users', set())
            online_users.discard(user_id)
            # Update cache
            cache.set('online_users', online_users, 300)
            print(f"User {user_id} marked as offline")
        except Exception as e:
            print(f"Error setting user offline: {e}")
