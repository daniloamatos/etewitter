from django.http import HttpResponse
from django.shortcuts import render
from main.models import Message
from django.core.cache import cache
from django.db.models import Q
from register.models import Usuario
def lobby(request, senderid, receiverid):
    user = request.user
    lastuser = Usuario.objects.last()
    if user.id != senderid:
        return HttpResponse("algo deu errado!")
    elif lastuser.id < receiverid:
        return HttpResponse("algo deu errado!")
    else:
        receiver = Usuario.objects.get(id=receiverid)
        message = list(Message.objects.filter(Q(receiver=user) | Q(sender=user), Q(receiver=receiver) | Q(sender=receiver)))
        return render(request, 'chat/lobby.html', {'user':user, 'receiver':receiver, 'messages':message})