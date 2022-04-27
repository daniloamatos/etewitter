
from django.http import HttpResponseNotFound, HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from register.models import Usuario
from django.contrib.auth import login as authLogin, authenticate
from .forms import LoginForm
from django.contrib.auth.hashers import check_password
from check.views import checkIfUsernameExists
from django.contrib.auth.decorators import user_passes_test

@user_passes_test(lambda u: not Usuario.is_authenticated, login_url='/')
def login(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            username = request.POST['usuario']
            password = request.POST['senha']
            check = checkIfUsernameExists(request, username)
            if check is True:
                u = Usuario.objects.filter(username__iexact=username).first()
                checkpa = check_password(password, u.password)
                if checkpa:
                    user=authenticate(username=username, password=password)
                    if u.is_active:  
                        Usuario.is_authenticated = True
                        authLogin(request, user)
                        return redirect("/")
                    else:
                        return HttpResponseNotFound('<h1>Usuario nao ativo.</h1>')
                else:
                    messages.error(request, 'Nome de usuário e/ou senha invalidos.')
            else:
                messages.error(request, 'Nome de usuário e/ou senha invalidos.')
        else:
            messages.error(request, 'Digite informações validas.')
    else: 
        form = LoginForm()
        return render(request, 'login/login.html', {"form":form})
    return render(request, 'login/login.html')