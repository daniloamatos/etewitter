from django.contrib import messages
from django.contrib.auth import authenticate, login as authLogin
from django.http import HttpResponse
from django.shortcuts import redirect, render

from change.views import email
from .forms import LoginForm


def login(request):
    if request.user.is_authenticated:
        return redirect('/')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['usuario'],
                password=form.cleaned_data['senha'],
            )
            if user is not None and user.is_active:
                authLogin(request, user)
                user.isAuthenticated = True
                user.save(update_fields=['isAuthenticated'])
                return redirect('/')
            messages.error(request, 'Nome de usuário e/ou senha invalidos.')
        else:
            messages.error(request, 'Digite informações validas.')
    else:
        form = LoginForm()
    return render(request, 'login/login.html', {'form': form})


def forgotpass(request):
    if request.method == 'POST':
        email(request, request.POST.get('email', '').strip())
        return HttpResponse(
            'Se o email estiver cadastrado, enviaremos instruções para recuperação.'
        )
    return render(request, 'login/forgotpass.html')
