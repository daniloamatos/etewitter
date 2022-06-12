from django.shortcuts import render
from main.models import Tweet
from register.models import Usuario

def search(request, **query):
    query = request.GET['query']
    print(query)
    if request.method == 'GET':
        result1 = Usuario.objects.filter(username__icontains=query)
        result2 = Tweet.objects.filter(tweet__icontains=query)
        result3 = Usuario.objects.filter(name__icontains=query)
        return render(request, "main/searchresult.html", {'result1':result1, 'result2':result2, 'result3':result3, 'query':query})
    