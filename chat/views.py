from django.shortcuts import render
from chat.models import Message
from django.core.cache import cache
from datetime import datetime
def lobby(request):
    message = Message.objects.all()
    return render(request, 'chat/lobby.html', {'messages':message})