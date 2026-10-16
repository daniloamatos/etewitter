from main.models import Notification, Replys
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils.translation import gettext as _


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
    # Prévia da publicação que gerou a notificação (para mostrar o conteúdo).
    target_text = ''
    target_image = ''
    target_kind = ''
    if reply is not None:
        target_text = reply.body or ''
        target_image = reply.image.url if reply.image else ''
        target_kind = 'reply'
    elif tweet is not None:
        target_text = tweet.tweet or ''
        target_image = tweet.image.url if tweet.image else ''
        target_kind = 'tweet'
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
                    'id': str(notif.pk),
                    'notification': body,
                    'notification_type': notification_type,
                    'target': {
                        'kind': target_kind,
                        'text': target_text,
                        'image': target_image,
                    },
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


def notify_reply_thread(reply, direct_parent):
    """Notify authors along the parent chain, naming the direct parent in the UI."""
    target_user = direct_parent.user if isinstance(direct_parent, Replys) else direct_parent.tweetAuthor
    authors = {reply.tweet.tweetAuthor_id: reply.tweet.tweetAuthor}
    authors.update({person.pk: person for person in reply.tweet.mentions.all()})
    pending = [direct_parent] if isinstance(direct_parent, Replys) else []
    visited = set()
    while pending:
        parent = pending.pop()
        if parent.pk in visited:
            continue
        visited.add(parent.pk)
        authors[parent.user_id] = parent.user
        authors.update({person.pk: person for person in parent.mentions.all()})
        pending.extend(parent.reply.select_related('user').all())

    newly_mentioned = set(reply.mentions.values_list("pk", flat=True))
    for recipient in authors.values():
        if recipient.pk != reply.user_id and recipient.pk not in newly_mentioned:
            create_notification(
                user=recipient,
                actor=reply.user,
                notification_type='reply',
                body=_('%(name)s respondeu a @%(username)s') % {
                    'name': reply.user.name, 'username': target_user.username,
                },
                linkzaocarai=reply.replyLink,
                reply=reply,
                tweet=reply.tweet,
            )


def notify_post_interaction(post, actor, kind):
    is_reply = isinstance(post, Replys)
    owner = post.user if is_reply else post.tweetAuthor
    recipients = {person.pk: person for person in post.mentions.all()}
    recipients[owner.pk] = owner
    if kind == 'like':
        own_text = _('%(name)s curtiu sua resposta') if is_reply else _('%(name)s curtiu seu tweet')
        mentioned_text = _('%(name)s curtiu uma publicação em que você foi mencionado')
    else:
        own_text = _('%(name)s retweetou sua resposta') if is_reply else _('%(name)s retweetou seu tweet')
        mentioned_text = _('%(name)s retweetou uma publicação em que você foi mencionado')
    for recipient in recipients.values():
        create_notification(
            user=recipient, actor=actor, notification_type=kind,
            body=(own_text if recipient.pk == owner.pk else mentioned_text) % {'name': actor.name},
            linkzaocarai=post.replyLink if is_reply else post.tweetLink,
            tweet=post.tweet if is_reply else post, reply=post if is_reply else None,
        )
