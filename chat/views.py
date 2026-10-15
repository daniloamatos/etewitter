from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404
from main.models import Message
from .unread import mark_conversation_read
from django.core.cache import cache
from django.db.models import Q
from register.models import Usuario
from django.contrib.auth.decorators import login_required
@login_required(login_url='/login')
def lobby(request, senderid, receiverid):
    user = request.user
    if user.id != senderid:
        return HttpResponse("algo deu errado!")
    elif user.id == receiverid:
        return HttpResponse("algo deu errado!")
    else:
        receiver = get_object_or_404(Usuario, id=receiverid)
        message = list(Message.objects.filter(Q(receiver=user) | Q(sender=user), Q(receiver=receiver) | Q(sender=receiver)))
        if message:
            mark_conversation_read(user, receiver.id, max(item.pk for item in message))
        return render(request, 'chat/lobby.html', {'user':user, 'receiver':receiver, 'chat_messages':message})