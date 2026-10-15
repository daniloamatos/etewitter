from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from main.models import Message


def broadcast_unread(user):
    async_to_sync(get_channel_layer().group_send)(
        user.username + 'notifications', {'type': 'unread_messages'},
    )


def mark_conversation_read(user, sender_id, through_id):
    updated = Message.objects.filter(
        receiver=user, sender_id=sender_id, pk__lte=through_id, is_read=False,
    ).update(is_read=True)
    if updated:
        broadcast_unread(user)
