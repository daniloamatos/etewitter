from django.shortcuts import render
from django.http import request
from django.http import HttpResponse
from django.shortcuts import render,  redirect
from django.contrib import messages
from .models import Tweet
from .forms import tweetForm
from django.contrib.auth.decorators import user_passes_test
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from check.views import checkIfUsernameExists, checkIfEmailExists


# Create your views here.
def home(request):
    return render(request, "main/home.html", {})

def tweet(request):
    if request.method == "POST":
        form = tweetForm(request.POST)
        if form.is_valid():
            simpanIp = form.save(commit=False)
            simpanIp.tweetAuthor = request.user.id
            simpanIp.save()
            form.save()
    else:
        form = tweetForm()
        return render(request, "main/home.html", {"form":form})
    return redirect("/")