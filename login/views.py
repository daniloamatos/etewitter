from django.contrib import messages
from django.contrib.auth import authenticate, login as authLogin
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _

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
                return redirect('/')
            messages.error(request, _('Nome de usuário e/ou senha invalidos.'))
        else:
            messages.error(request, _('Digite informações validas.'))
    else:
        form = LoginForm()
    return render(request, 'login/login.html', {'form': form})


def forgotpass(request):
    if request.method == 'POST':
        email(request, request.POST.get('email', '').strip())
        return HttpResponse(
            _('Se o email estiver cadastrado, enviaremos instruções para recuperação.')
        )
    return render(request, 'login/forgotpass.html')
