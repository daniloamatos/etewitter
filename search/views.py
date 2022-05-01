from django.shortcuts import render
from main.models import Tweet
from register.models import Usuario

def search(request, **query):
    query = request.GET['query']
    if request.method == 'GET':
        result1 = Usuario.objects.filter(username__contains=query)
        result2 = Tweet.objects.filter(tweet__contains=query)
        return render(request, "main/searchresult.html", {'result1':result1, 'result2':result2, 'query':query})
    