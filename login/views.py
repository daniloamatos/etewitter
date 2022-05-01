
from django.shortcuts import render, redirect
from django.contrib import messages
from register.models import Usuario
from django.contrib.auth import login as authLogin
from .forms import LoginForm
from django.contrib.auth.hashers import check_password
from check.views import checkIfUsernameExists
from .authenticate import authentication


def login(request):
    if str(request.user) != 'AnonymousUser':
        return redirect('/')
    else:
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
                        user=authentication.authenticateCustom(request, username=username, password=password)
                        if u.is_active:  
                            authLogin(request, user)
                            u.isAuthenticated = True
                            return redirect("/")
                        else:
                            messages.error(request, 'Usuario nao ativo.')
                    else:
                        messages.error(request, 'Nome de usuário e/ou senha invalidos.')
                else:
                    messages.error(request, 'Nome de usuário e/ou senha invalidos.')
            else:
                messages.error(request, 'Digite informações validas.')
        else: 
            form = LoginForm()
            return render(request, 'login/login.html', {"form":form})
        return render(request, 'login/login.html', {"form":form})


