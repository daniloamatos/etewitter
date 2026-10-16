from .models import Message, Notification, SavedItems


def unread_messages(request):
    is_auth = request.user.is_authenticated
    return {
        'has_unread_messages': is_auth and
            Message.objects.filter(receiver=request.user, is_read=False).exists(),
        'has_unread_notifications': is_auth and
            Notification.objects.filter(user=request.user, is_read=False).exclude(linkzaocarai__startswith='messages/').exists(),
    }


def saved_items(request):
    """Retorna os IDs de tweets e replies salvos pelo usuário autenticado."""
    if not request.user.is_authenticated:
        return {'saved_tweet_ids': [], 'saved_reply_ids': []}
    saved = SavedItems.objects.filter(user=request.user)
    tweet_ids = list(saved.filter(tweet__isnull=False).values_list('tweet_id', flat=True))
    reply_ids = list(saved.filter(reply__isnull=False).values_list('reply_id', flat=True))
    return {
        'saved_tweet_ids': tweet_ids,
        'saved_reply_ids': reply_ids,
    }
