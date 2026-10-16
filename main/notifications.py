from main.models import Notification
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def create_notification(user, actor, notification_type, body, linkzaocarai, tweet=None, reply=None):
    if not user or not actor or user == actor:
        return None
    notif = Notification.objects.create(
        user=user,
        actor=actor,
        notification_type=notification_type,
        body=body,
        linkzaocarai=linkzaocarai,
        tweet=tweet,
        reply=reply,
        is_read=False,
    )
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                user.username + 'notifications',
                {
                    'type': 'unread_notifications',
                    'unread': True,
                }
            )
            avatar_url = '/static/images/default-profile.svg'
            if actor.profilepic and actor.profilepic.name != 'default/default_profile_400x400.png':
                avatar_url = actor.profilepic.url
            async_to_sync(channel_layer.group_send)(
                user.username + 'notifications',
                {
                    'type': 'new_notification',
                    'notification': body,
                    'actor': {
                        'username': actor.username,
                        'name': actor.name,
                        'avatar': avatar_url,
                    },
                    'url': f'/{linkzaocarai}',
                }
            )
    except Exception:
        pass
    return notif
