
from django.shortcuts import render
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from register.models import Usuario
from check.views import checkIfUsernameExists
from main.models import Tweet,Like
from main.forms import tweetForm

def userprofile(request,username):
    username = username
    if  checkIfUsernameExists(request, username):
        if request.method == "POST":
            form = tweetForm(request.POST)
            if 'image' in request.FILES:
                simpanIp = form.save(commit=False)
                simpanIp.image = request.FILES['image']
                simpanIp.tweetAuthor = request.user
                simpanIp.save()
                form.save()
            elif form.data['tweet']:
                simpanIp = form.save(commit=False)
                simpanIp.tweetAuthor = request.user
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
        #next = request.POST.get('next', '/')
        #return redirect(next)


