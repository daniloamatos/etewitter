from django.shortcuts import render
from django.shortcuts import render,  redirect
from .forms import tweetForm
from .models import Tweet
from register.models import Usuario

# Create your views here.

def home(request):
    if str(request.user) == 'AnonymousUser':
        return redirect('/index')
    else:
        tweets = Tweet.objects.filter(tweetAuthor=request.user)
        if request.method == "POST":
            form = tweetForm(request.POST)
            if form.is_valid():
                simpanIp = form.save(commit=False)
                simpanIp.tweetAuthor = request.user
                simpanIp.save()
                form.save()
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
    