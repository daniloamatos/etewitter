
import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from main.models import Notification
from register.models import Usuario
from django.db.models import Q
from datetime import datetime

class NotificationConsumer(WebsocketConsumer):

    def connect(self):
        user = self.scope['user']
        self.room_group_name =  user.username + 'notifications'
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

    def new_notification(self,event):
        notification = event['notification']
        self.send(text_data=json.dumps({
            'type':'notification',
            'notification':notification,
        }))

        