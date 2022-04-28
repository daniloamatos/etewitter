from django.shortcuts import redirect
from django.contrib.auth import logout as django_logout
# Create your views here.

def logout(request):
    django_logout(request)
    return redirect('/index')
    