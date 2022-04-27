from django.shortcuts import render
from django.shortcuts import render,  redirect
from .forms import tweetForm
from django.contrib.auth.decorators import login_required
from .models import Tweet
from register.models import Usuario


# Create your views here.
@login_required(login_url='/index')
def home(request):
    return render(request, "main/homepage.html", {})

def index(request):
    return render(request, "main/index.html", {})

@login_required(login_url='/index')
def tweet(request):
    tweets = Tweet.objects.filter(tweetAuthor=request.user.id)
    if request.method == "POST":
        form = tweetForm(request.POST)
        if form.is_valid():
            simpanIp = form.save(commit=False)
            simpanIp.tweetAuthor = request.user.id
            simpanIp.save()
            form.save()
    else:
        form = tweetForm()
        return render(request, "main/homepage.html", {"form":form, "tweets":tweets})
    return redirect("/")