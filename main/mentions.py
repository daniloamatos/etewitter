"""Resolve explicit handles and remember the recipients of a publication."""
import re

from django.db.models.functions import Lower
from django.utils.translation import gettext as _

from register.models import Usuario

MENTION_RE = re.compile(r'(?<![\w@])@([A-Za-z0-9]{4,25})(?![\w@])')


def mentioned_users(text):
    handles = {match.group(1).lower() for match in MENTION_RE.finditer(text or '')}
    if not handles:
        return {}
    return {user.username.lower(): user for user in
            Usuario.objects.annotate(handle=Lower('username')).filter(handle__in=handles)}


def register_mentions(post):
    from main.models import Replys
    from main.notifications import create_notification

    is_reply = isinstance(post, Replys)
    users = mentioned_users(post.body if is_reply else post.tweet)
    post.mentions.set(users.values())
    actor = post.user if is_reply else post.tweetAuthor
    for user in users.values():
        create_notification(
            user=user, actor=actor, notification_type='mention',
            body=(_('%(name)s te mencionou em uma resposta') if is_reply else
                  _('%(name)s te mencionou em um tweet')) % {'name': actor.name},
            linkzaocarai=post.replyLink if is_reply else post.tweetLink,
            tweet=post.tweet if is_reply else post, reply=post if is_reply else None,
        )
