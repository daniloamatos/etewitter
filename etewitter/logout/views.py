from django.shortcuts import render
from register.models import Usuario
from django.contrib.auth.decorators import login_required
# Create your views here.

@login_required(login_url='/login')
def logout(request):
    Usuario.is_authenticated = False
    return render(request,"logout/logout.html", {})
    