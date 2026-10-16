import json

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views.decorators.http import require_POST

from main.models import Message
from .unread import mark_conversation_read
from django.db.models import Q
from register.models import Usuario
from django.contrib.auth.decorators import login_required
from django.utils.translation import gettext as _


@login_required(login_url='/login')
def lobby(request, senderid, receiverid):
    user = request.user
    if user.id != senderid:
        return HttpResponse(_("algo deu errado!"))
    elif user.id == receiverid:
        return HttpResponse(_("algo deu errado!"))
    else:
        receiver = get_object_or_404(Usuario, id=receiverid)
        message = list(
            Message.objects.filter(
                Q(sender=user, receiver=receiver) | Q(sender=receiver, receiver=user)
            ).select_related('sender').order_by('publishDate', 'id')
        )
        if message:
            mark_conversation_read(user, receiver.id)
        return render(request, 'chat/lobby.html', {'user': user, 'receiver': receiver, 'chat_messages': message})


@login_required(login_url='/login')
@require_POST
def save_public_key(request):
    """Guarda a chave pública (JWK) do usuário autenticado.

    A chave privada correspondente nunca chega ao servidor — fica só no
    navegador do usuário (IndexedDB).
    """
    try:
        payload = json.loads(request.body or b'{}')
    except ValueError:
        payload = {}
    key = payload.get('public_key', '')
    if not isinstance(key, str) or not key or len(key) > 4000:
        return JsonResponse({'status': 'error', 'error': _('Chave pública inválida.')}, status=400)
    request.user.public_key = key
    request.user.save(update_fields=['public_key'])
    return JsonResponse({'status': 'ok'})


@login_required(login_url='/login')
def get_public_key(request, userid):
    """Devolve a chave pública de um usuário (para derivar a chave da conversa)."""
    person = get_object_or_404(Usuario, id=userid)
    return JsonResponse({'public_key': person.public_key or ''})
