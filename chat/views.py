from django.shortcuts import render
from chat.models import Message
from django.core.cache import cache
from datetime import datetime
def lobby(request):
    """id = 2
    if cache.get(id):
        now = datetime.now()
        message = cache.get(id)
        print("cache")
        print(datetime.now() - now)
    else:
        now = datetime.now()"""
    message = Message.objects.all()
    return render(request, 'chat/lobby.html', {'messages':message})