
import json
import base64
import binascii
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from main.models import Message, Chat
from main.image_utils import (
    ALLOWED_IMAGE_EXTENSIONS,
    MAX_IMAGE_UPLOAD_SIZE,
    MAX_IMAGE_UPLOAD_SIZE_MB,
)
from register.models import Usuario
from django.db.models import Q
from django.utils import timezone
from .unread import broadcast_unread, mark_conversation_read


def decode_image(data_url):
    """Converte um data URL (data:image/...;base64,...) em ContentFile.

    Retorna uma tupla (arquivo, erro). O arquivo é None quando não veio imagem.
    """
    if not isinstance(data_url, str) or not data_url.startswith('data:image/'):
        return None, None
    try:
        header, encoded = data_url.split(',', 1)
        if 'base64' not in header:
            return None, 'Formato de imagem não suportado.'
        ext = header.split('/')[1].split(';')[0].lower()
        if ext not in ALLOWED_IMAGE_EXTENSIONS:
            return None, 'Formato não suportado. Use JPG, PNG, GIF ou WEBP.'
        if ext == 'jpeg':
            ext = 'jpg'
        raw = base64.b64decode(encoded)
    except (ValueError, binascii.Error):
        return None, 'Não foi possível ler a imagem.'
    if len(raw) > MAX_IMAGE_UPLOAD_SIZE:
        return None, 'A imagem é muito grande. O limite é {0} MB.'.format(MAX_IMAGE_UPLOAD_SIZE_MB)
    return ContentFile(raw, name='chat.{0}'.format(ext)), None


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
        try:
            text_data_json = json.loads(text_data)
        except (TypeError, ValueError):
            return
        if text_data_json.get('type') == 'read':
            try:
                through_id = int(text_data_json.get('through_id', 0))
            except (TypeError, ValueError):
                return
            mark_conversation_read(self.scope['user'],
                                   self.scope["url_route"]["kwargs"]['receiverid'], through_id)
            return
        message = text_data_json.get('message', '')
        if not isinstance(message, str):
            message = ''
        message = message.strip()
        image_file, image_error = decode_image(text_data_json.get('image'))
        if image_error:
            self.send_error(image_error)
            return
        if (not message and image_file is None) or len(message) > 250:
            return
        user = self.scope['user']
        receiver = Usuario.objects.filter(id=int(
            self.scope["url_route"]["kwargs"]['receiverid']
        )).first()
        if receiver is None or receiver.id == user.id:
            self.close()
            return
        try:
            saved_message = self.save_message(message, user, receiver, image_file)
        except ValidationError as exc:
            self.send_error(' '.join(exc.messages))
            return
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type':'chat_message',
                'message':message,
                'message_id': saved_message.pk,
                'image': saved_message.image.url if saved_message.image else None,
                'username':user.username,
                'receiver':receiver.username,
                'time': timezone.localtime(saved_message.publishDate).strftime('%H:%M')
            }
        )

    def chat_message(self,event):
        message = event['message']
        user = event['username']
        self.send(text_data=json.dumps({
            'type':'chat',
            'message_id': event['message_id'],
            'message':message,
            'image': event.get('image'),
            'username':user,
            'time': event.get('time') or timezone.localtime(timezone.now()).strftime('%H:%M')
        }))

    def send_error(self, message):
        self.send(text_data=json.dumps({'type': 'error', 'error': message}))

    def save_message(self, message, user, receiver, image_file=None):
        if image_file is not None:
            saved_message = Message.objects.create(sender=user, body=message, receiver=receiver, image=image_file)
        else:
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
