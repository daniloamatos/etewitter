
from django.shortcuts import redirect, render
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from register.models import Usuario
from check.views import checkIfUsernameExists
from main.models import Tweet,Like,Replys
from main.forms import replyForm,tweetForm
from main.views import generateLink

def userprofile(request,username):
    username = username
    if  checkIfUsernameExists(request, username):
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
            form = tweetForm
        jname = Usuario.objects.filter(username__iexact=username).values_list('name').first()
        user = Usuario.objects.get(username__iexact=username)
        checkUser = request.user
        tweets = Tweet.objects.filter(tweetAuthor=user.id)
        return render(request, "userprofile/userprofile.html", {"form":form,"jusername":username, "jname":jname[0], "user":user, "tweets":tweets, 'checkUser':checkUser, 'usuario':checkUser})
    else:
        return HttpResponse("essa conta não existe, tente procurar por outra coisa")



def likereply(request,**username):
    if request.method == 'POST':
        user = request.user
        reply_id = request.POST['replyid']
        reply_obj = Replys.objects.get(id = reply_id)
        usuario = Usuario.objects.get(username = user)
        if usuario in reply_obj.likes.all():
            reply_obj.likes.remove(usuario)
        else:
            reply_obj.likes.add(usuario)
        
        like, created = Like.objects.get_or_create(user=usuario, tweet_id=reply_id)

        if not created:
            if like.value=='Like':
                like.value='Unlike'
            else:
                like.value='Like'

            reply_obj.save()
            like.save()
        data = {
            'value': like.value,
            'likes': reply_obj.likes.all().count()
        }

        return JsonResponse(data, safe=False)

def like (request, **username):
    if request.method == 'POST':
        user = request.user
        tweet_id = request.POST['tweetid']
        tweet_obj = Tweet.objects.get(id = tweet_id)
        usuario = Usuario.objects.get(username = user)

        if usuario in tweet_obj.likes.all():
            tweet_obj.likes.remove(usuario)
        else:
            tweet_obj.likes.add(usuario)
        like, created = Like.objects.get_or_create(user=usuario, tweet_id=tweet_id)

        if not created:
            if like.value=='Like':
                like.value='Unlike'
            else:
                like.value='Like'

            tweet_obj.save()
            like.save()
        data = {
            'value': like.value,
            'likes': tweet_obj.likes.all().count()
        }

        return JsonResponse(data, safe=False)

def reply (request, **username):
    if request.method == 'POST':
        user = request.user
        tweet_id = request.POST['tweetid']
        tweet_obj = Tweet.objects.get(id = tweet_id)
        form = replyForm(request.POST)
        if 'image' in request.FILES:
            instance = form.save(commit=False)
            instance.image = request.FILES['image']
            instance.user = user
            instance.tweet = tweet_obj
            instance.body = request.POST['body']
            instance.replyLink = generateLink(request)
            instance.save()
            form.save()
        elif form.data['body']:
            instance = form.save(commit=False)
            instance.user = user
            instance.tweet = tweet_obj
            instance.body = request.POST['body']
            instance.replyLink = generateLink(request)
            instance.save()
            form.save()
        else:
            messages.error(request, 'O tweet precisa haver algum caractere ou imagem.')
    return redirect(request.POST['next'])


def requesttweet (request, username, random):
    checkUser = request.user
    form = replyForm()
    if Tweet.objects.filter(tweetLink=f'{username}/status/{random}'):
        tweet = Tweet.objects.filter(tweetLink=f'{username}/status/{random}') 
        qs = Replys.objects.filter(tweet=tweet[0])
        notReply = True
        return render(request, "userprofile/tweet.html", {'tweet':tweet, 'usuario':checkUser, 'form':form, 'qs':qs, 'notReply':notReply})
    else:
        notReply = False
        reply = Replys.objects.filter(replyLink=f'{username}/status/{random}') 
        return render(request, "userprofile/tweet.html", {'tweet':reply, 'usuario':checkUser, 'form':form, 'notReply':notReply})
    
