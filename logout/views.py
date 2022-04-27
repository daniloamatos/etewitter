from django.shortcuts import redirect
from django.contrib.auth import logout as django_logout
from register.models import Usuario
# Create your views here.

def logout(request):
    request.user.is_authenticated = False
    Usuario.is_authenticated = False
    django_logout(request)
    return redirect('/index')
    