
import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from main.models import Message, Chat
from register.models import Usuario
from django.db.models import Q
from datetime import datetime

class ChatConsumer(WebsocketConsumer):

    def connect(self):
        receiverid = int(self.scope["url_route"]["kwargs"]['receiverid'])
        userid = self.scope['user'].id
        if(userid < receiverid):
            self.room_group_name = str(self.scope['user'].id) + "-" + self.scope["url_route"]["kwargs"]['receiverid']
        else:
            self.room_group_name =  self.scope["url_route"]["kwargs"]['receiverid'] + "-" + str(self.scope['user'].id)
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()

    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        user = text_data_json['username']
        receiver = text_data_json['receiver']
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type':'chat_message',
                'message':message,
                'username':user,
                'receiver':receiver
            }
        )
        self.save_message(message, user,receiver)

    def chat_message(self,event):
        message = event['message']
        user = event['username']
        self.send(text_data=json.dumps({
            'type':'chat',
            'message':message,
            'username':user
        }))

    def save_message(self, message, user,receiver):
        user = Usuario.objects.get(username=user)
        receiver = Usuario.objects.get(username=receiver)
        Message.objects.create(sender = user, body=message, receiver=receiver)
        try:
            chat = Chat.objects.get(Q(sender = user)| Q(receiver=user), Q(sender = receiver)| Q(receiver = receiver))
            chat.publishDate = datetime.now()
            chat.save()
        except:
            Chat.objects.update_or_create(sender = user, receiver = receiver)
        message = list(Message.objects.filter(Q(receiver=user) | Q(sender=user), Q(receiver=receiver) | Q(sender=receiver)))
        