

import random
from django.http import HttpResponse
from django.shortcuts import render,  redirect
from .forms import tweetForm
from .models import Tweet, SavedItems as SavedItemsclass, Follower, Message, Report, Chat
from register.models import Usuario
from django.contrib import messages
from datetime import datetime
from django.db.models import Q

# Create your views here.

def home(request):
    if str(request.user) == 'AnonymousUser':
        return redirect('/index')
    else:
        tweetsSelf = Tweet.objects.filter(tweetAuthor=request.user)
        try:
            following = Follower.objects.filter(follower_id = request.user.id).values_list("following_id").all()
            tweetsFollowing = Tweet.objects.filter(tweetAuthor_id__in = following)
            tweets = tweetsSelf | tweetsFollowing
        except:
            tweets = tweetsSelf
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

def saveditems(request):
    user = request.user    
    tweet = SavedItemsclass.objects.filter(user = user)
    return render(request, 'main/saveditems.html', {'user':user, 'tweet':tweet})


def follow(request):
    if request.method == 'POST':
        user = request.user
        following = Usuario.objects.get(id = request.POST['userP'])
        if Follower.objects.filter(following_id = following.id, follower = user.id):
            Follower.objects.filter(follower = user, following = following).delete()
            following.followersC -=1
            following.save()
            user.followingC -= 1
            user.save()
            return redirect(request.POST['next'])
        else:
            Follower.objects.create(follower = user, following = following)
            following.followersC +=1
            following.save()
            user.followingC += 1
            user.save()
            return redirect(request.POST['next'])

def sendmessage(request, sender, receiver, message, next):
    if request.method == 'POST':
        Message.objects.create(
            sender = sender,
            receiver = receiver,
            body = message
        )
        return redirect(next)

def delete(request):
    if request.method == "POST":
        Tweet.objects.get(id = request.POST['tweetid']).delete()
        messages.success(request, 'Tweet deletado.')
        return redirect('/')
    
def report(request):
    x9 = request.user
    tweet = Tweet.objects.get(id = request.POST['tweetid'])
    reason = request.POST['reason']
    Report.objects.create(
        x9 = x9,
        tweet = tweet,
        reason = reason
    )
    messages.success(request, 'Denuncia registrada.')
    return redirect(request.POST['next'])
