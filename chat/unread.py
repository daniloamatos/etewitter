from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils.dateparse import parse_datetime
from main.models import Message


def broadcast_unread(user):
    async_to_sync(get_channel_layer().group_send)(
        user.username + 'notifications', {'type': 'unread_messages'},
    )


def mark_conversation_read(user, sender_id, through=None):
    """Marca como lidas as mensagens que ``user`` recebeu de ``sender_id``.

    ``through`` é a data/hora (ISO 8601) da última mensagem lida; quando
    informada, só marca o que veio até ela. Como as PKs agora são UUIDs,
    a ordenação temporal usa ``publishDate`` em vez de ``pk``.
    """
    messages = Message.objects.filter(
        receiver=user, sender_id=sender_id, is_read=False,
    )
    if through:
        moment = parse_datetime(through) if isinstance(through, str) else through
        if moment is not None:
            messages = messages.filter(publishDate__lte=moment)
    updated = messages.update(is_read=True)
    if updated:
        broadcast_unread(user)
