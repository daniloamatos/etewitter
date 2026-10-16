from django.http import Http404
from django.shortcuts import get_object_or_404
import uuid
from .models import Replys, Tweet


def post_target(request):
    kind = request.POST.get('content_type', 'tweet')
    if kind not in ('tweet', 'reply'):
        raise Http404('Tipo de publicação inválido.')
    try:
        target_id = uuid.UUID(str(request.POST.get('tweetid', '')))
    except (ValueError, TypeError, AttributeError):
        raise Http404('Publicação inválida.')
    target = get_object_or_404(Replys if kind == 'reply' else Tweet, pk=target_id)
    return kind, target
