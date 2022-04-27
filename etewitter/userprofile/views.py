from unicodedata import name
from django.shortcuts import render,  redirect, get_object_or_404
from django.http import HttpResponse
from register.models import Usuario
from check.views import checkIfUsernameExists
from main.models import Tweet
from main.forms import tweetForm
from django.forms.models import model_to_dict

def userprofile(request,username):
    username = username
    if  checkIfUsernameExists(request, username):
        jname = Usuario.objects.filter(username=username).values_list('name').first()
        user = Usuario.objects.get(username=username)
        tweets = Tweet.objects.filter(tweetAuthor=user.id)
        return render(request, "userprofile/userprofile.html", {"jusername":username, "jname":jname[0], "user":user, "tweets":tweets})
    else:
        return HttpResponse("essa conta não existe, tente procurar por outra coisa")

def like (request, **username):
    if request.method == 'POST':
        print(request.POST['tweetid'])
        person = get_object_or_404(Tweet, id=request.POST['tweetid'])
        person.likes += 1
        person.save()
        next = request.POST.get('next', '/')
        return redirect(next)


