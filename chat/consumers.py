
import json
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from main.models import Message, Chat
from register.models import Usuario
from django.db.models import Q
from django.utils import timezone
from .unread import broadcast_unread, mark_conversation_read

class ChatConsumer(WebsocketConsumer):

    def connect(self):
        if self.scope['user'].is_anonymous:
            self.close()
            return
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
        if text_data_json.get('type') == 'read':
            try:
                through_id = int(text_data_json.get('through_id', 0))
            except (TypeError, ValueError):
                return
            mark_conversation_read(self.scope['user'],
                                   self.scope['url_route']['kwargs']['receiverid'], through_id)
            return
        message = text_data_json.get('message', '')
        if not isinstance(message, str) or not message.strip() or len(message) > 250:
            return
        user = self.scope['user']
        receiver = Usuario.objects.filter(id=int(
            self.scope["url_route"]["kwargs"]['receiverid']
        )).first()
        if receiver is None or receiver.id == user.id:
            self.close()
            return
        saved_message = self.save_message(message, user, receiver)
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type':'chat_message',
                'message':message,
                'message_id': saved_message.pk,
                'username':user.username,
                'receiver':receiver.username
            }
        )

    def chat_message(self,event):
        message = event['message']
        user = event['username']
        self.send(text_data=json.dumps({
            'type':'chat',
            'message_id': event['message_id'],
            'message':message,
            'username':user
        }))

    def save_message(self, message, user, receiver):
        saved_message = Message.objects.create(sender=user, body=message, receiver=receiver)
        chat = Chat.objects.filter(
            Q(sender=user) | Q(receiver=user),
            Q(sender=receiver) | Q(receiver=receiver),
        ).first()
        if chat:
            chat.publishDate = timezone.now()
            chat.save()
        else:
            Chat.objects.create(sender=user, receiver=receiver)
        broadcast_unread(receiver)
        return saved_message

    def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            async_to_sync(self.channel_layer.group_discard)(self.room_group_name, self.channel_name)
