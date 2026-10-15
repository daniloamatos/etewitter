from .models import Message


def unread_messages(request):
    return {'has_unread_messages': request.user.is_authenticated and
            Message.objects.filter(receiver=request.user, is_read=False).exists()}
