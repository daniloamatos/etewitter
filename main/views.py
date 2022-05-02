

import random
from django.shortcuts import render,  redirect
from .forms import tweetForm
from .models import Tweet
from register.models import Usuario
from django.contrib import messages
from datetime import datetime

# Create your views here.

def home(request):
    if str(request.user) == 'AnonymousUser':
        return redirect('/index')
    else:
        tweets = Tweet.objects.filter(tweetAuthor=request.user)
        if request.method == "POST":
            form = tweetForm(request.POST)
            if 'image' in request.FILES:
                simpanIp = form.save(commit=False)
                simpanIp.image = request.FILES['image']
                simpanIp.tweetAuthor = request.user
                simpanIp.tweetLink = generateLink(request)
                simpanIp.save()
                form.save()
            elif form.data['tweet']:
                simpanIp = form.save(commit=False)
                simpanIp.tweetAuthor = request.user
                simpanIp.tweetLink = generateLink(request)
                simpanIp.save()
                form.save()
            else:
                messages.error(request, 'O tweet precisa haver algum caractere ou imagem.')
        else:
            usuario = Usuario.objects.get(username=request.user.username)
            form = tweetForm()
            return render(request, "main/homepage.html", {"form":form, "tweets":tweets, 'usuario':usuario})
        return redirect("/")

def index(request):
    if str(request.user) != 'AnonymousUser':
        return redirect('/')
    else:
        return render(request, "main/index.html", {})

def generateLink(request):
    chars = '1234567890'
    randomstr = ''.join((random.choice(chars)) for x in range(30))
    _now = datetime.now()
    day=_now.strftime('%d')
    month=_now.strftime('%m')
    year=_now.strftime('%Y')
    link = str(f'{request.user.username}/status/{randomstr}{day}{month}{year}')
    return link