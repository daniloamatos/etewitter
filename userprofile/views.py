
from django.shortcuts import redirect, render
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from register.models import Usuario
from check.views import checkIfUsernameExists
from main.models import Tweet,Like,Replys,SavedItems, Follower, Chat
from main.forms import replyForm,tweetForm
from main.views import generateLink
from django.db.models import Q

def userprofile(request,username):
    followers = None
    following = None
    try:
        userprofileid = Usuario.objects.filter(username = username).values_list("id").all()

        um = Follower.objects.filter(follower_id__in = userprofileid).values_list("following_id").all()

        following = Usuario.objects.filter(id__in = um)
        
        dois = Follower.objects.filter(following_id__in = userprofileid).values_list("follower_id").all()

        followers = Usuario.objects.filter(id__in = dois)

    except:
        pass
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
        return render(request, "userprofile/userprofile.html", {"followers":followers,"following":following, "form":form,"jusername":username, "jname":jname[0], "userP":user, "tweets":tweets, 'checkUser':checkUser, 'usuario':checkUser})
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
        like, created = Like.objects.get_or_create(user=usuario, tweet_id=reply_obj.tweet_id)

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
        reply = False
        user = request.user
        tweet_id = request.POST['tweetid']
        try:
            tweet_obj = Tweet.objects.get(id = tweet_id)
        except:
            tweet_obj = Replys.objects.get(id = tweet_id)
            reply = True
        form = replyForm(request.POST)
        if 'image' in request.FILES:
            if reply:
                
                test = Replys.objects.create(
                    user = user,
                    tweet = tweet_obj.tweet,
                    reply = tweet_obj,
                    body = request.POST['body'],
                    image = request.FILES['image'],
                    replyLink = generateLink(request)
                )
                test.reply.add(tweet_obj)
                return redirect(request.POST['next'])
            else:
                instance = form.save(commit=False)
                instance.tweet = tweet_obj
                instance.image = request.FILES['image']
                tweet_obj.replysC += 1
                tweet_obj.save()
                instance.user = user
                instance.body = request.POST['body']
                instance.replyLink = generateLink(request)
                instance.save()
                form.save()
                return redirect(request.POST['next'])
        elif form.data['body']:
            if reply:
                test = Replys.objects.create(
                    user = user,
                    tweet = tweet_obj.tweet,
                    body = request.POST['body'],
                    replyLink = generateLink(request)
                )
                test.reply.add(tweet_obj)
                return redirect(request.POST['next'])
            else:
                instance = form.save(commit=False)
                instance.tweet = tweet_obj
                tweet_obj.replysC += 1
                tweet_obj.save()
                instance.user = user
                instance.body = request.POST['body']
                instance.replyLink = generateLink(request)
                instance.save()
                form.save()
                return redirect(request.POST['next'])
        else:
            messages.error(request, 'O tweet precisa haver algum caractere ou imagem.')
    return redirect(request.POST['next'])


def requesttweet (request, username, random):
    checkUser = request.user
    form = replyForm()
    if Tweet.objects.filter(tweetLink=f'{username}/status/{random}'):
        tweet = Tweet.objects.filter(tweetLink=f'{username}/status/{random}') 
        tweetObj = Tweet.objects.get(tweetLink=f'{username}/status/{random}')
        qs = Replys.objects.filter(tweet=tweet[0])
        notReply = True
        return render(request, "userprofile/tweet.html", {'tweet':tweet, 'usuario':checkUser, 'form':form, 'qs':qs, 'notReply':notReply, 'tweetObj':tweetObj})
    else:
        notReply = False
        reply = Replys.objects.filter(replyLink=f'{username}/status/{random}') 
        tweetObj = Replys.objects.get(replyLink=f'{username}/status/{random}') 
        qs = Replys.objects.filter(reply=reply[0])
        return render(request, "userprofile/tweet.html", {'tweet':reply, 'usuario':checkUser, 'form':form, 'qs':qs, 'notReply':notReply, 'tweetObj':tweetObj})
    
def save(request):
    if request.method == 'POST':
        user = request.user
        tweet_id = request.POST['tweetid']
        tweet = Tweet.objects.get(id = tweet_id)
        saveditems = SavedItems()
        if SavedItems.objects.filter(user = user):
            if SavedItems.objects.filter(tweet = tweet):
                SavedItems.objects.filter(user = user, tweet = tweet).delete()
                return redirect(request.POST['next'])
        saveditems.user = user
        saveditems.tweet = tweet
        saveditems.save()
        return redirect(request.POST['next'])

def message(request):
    user = request.user
    try:
        conversation = Chat.objects.filter(Q(sender = user)| Q(receiver=user))
    except:
        conversation = None
    return render(request, 'main/message.html', {'chats':conversation})
