
import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from main.models import Message
from register.models import Usuario
from django.db.models import Q
from datetime import datetime

class NotificationConsumer(WebsocketConsumer):

    def connect(self):
        user = self.scope['user']
        if user.is_anonymous:
            self.close()
            return
        self.room_group_name =  user.username + 'notifications'
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()
        self.unread_messages({})

    def new_notification(self,event):
        notification = event['notification']
        self.send(text_data=json.dumps({
            'type':'notification',
            'notification':notification,
            'actor': event.get('actor'),
            'url': event.get('url', '/notifications/'),
        }))


    def unread_messages(self, event):
        self.send(text_data=json.dumps({
            'type': 'unread_messages',
            'unread': Message.objects.filter(receiver=self.scope['user'], is_read=False).exists(),
        }))

    def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.channel_name)
