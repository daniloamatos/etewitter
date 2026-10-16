
import json
import base64
import binascii
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from main.models import Message, Chat
from register.models import Usuario
from django.db.models import Q
from django.utils import timezone
from django.utils.translation import gettext as _
from .unread import broadcast_unread, mark_conversation_read


# Limites do conteúdo JÁ CIFRADO. Os limites "reais" (5 MB de imagem, 250
# caracteres de texto) são garantidos pelo cliente antes de cifrar; aqui só
# evitamos payloads abusivos. O servidor não consegue ler nada disso.
MAX_ENCRYPTED_IMAGE_SIZE = 8 * 1024 * 1024
MAX_ENCRYPTED_MESSAGE_LENGTH = 2000


def decode_encrypted_image(payload):
    """Desembrulha a imagem cifrada (base64 de iv||ciphertext) vinda do cliente.

    Retorna (arquivo, erro). O arquivo é None quando não veio imagem.
    """
    if not payload:
        return None, None
    if not isinstance(payload, str):
        return None, _('Imagem inválida.')
    try:
        raw = base64.b64decode(payload, validate=True)
    except (ValueError, binascii.Error):
        return None, _('Não foi possível ler a imagem.')
    if len(raw) > MAX_ENCRYPTED_IMAGE_SIZE:
        return None, _('A imagem é muito grande.')
    return ContentFile(raw, name='chat.enc'), None


class ChatConsumer(WebsocketConsumer):

    def connect(self):
        if self.scope['user'].is_anonymous:
            self.close()
            return
        receiverid = self.scope["url_route"]["kwargs"]['receiverid']
        userid = str(self.scope['user'].id)
        first, second = sorted([userid, receiverid])
        self.room_group_name = first + "-" + second
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
            mark_conversation_read(
                self.scope['user'],
                self.scope["url_route"]["kwargs"]['receiverid'],
                text_data_json.get('through'),
            )
            return
        message = text_data_json.get('message', '')
        if not isinstance(message, str):
            message = ''
        message = message.strip()
        image_file, image_error = decode_encrypted_image(text_data_json.get('image'))
        if image_error:
            self.send_error(image_error)
            return
        if (not message and image_file is None) or len(message) > MAX_ENCRYPTED_MESSAGE_LENGTH:
            return
        user = self.scope['user']
        try:
            receiver = Usuario.objects.filter(id=self.scope["url_route"]["kwargs"]['receiverid']).first()
        except (ValidationError, ValueError):
            receiver = None
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
                'message_id': str(saved_message.pk),
                'image': saved_message.image.url if saved_message.image else None,
                'username':user.username,
                'receiver':receiver.username,
                'time': timezone.localtime(saved_message.publishDate).strftime('%H:%M'),
                'published': saved_message.publishDate.isoformat(),
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
            'time': event.get('time') or timezone.localtime(timezone.now()).strftime('%H:%M'),
            'published': event.get('published'),
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
