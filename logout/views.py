from django.shortcuts import redirect
from register.models import Usuario
# Create your views here.

def logout(request):
    Usuario.is_authenticated = False
    return redirect('/')
    