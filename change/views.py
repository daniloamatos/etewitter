from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from logout.views import logout
from register.models import Usuario
from register.tokens import account_activation_token
from .forms import ChangeName, ChangePass, ChangeUsername


@login_required(login_url='/login')
def changeName(request, *args):
    if request.method == 'POST':
        form = ChangeUsername(request.POST) if args else ChangeName(request.POST)
        if form.is_valid():
            value = form.cleaned_data['username' if args else 'name']
            if args:
                if Usuario.objects.filter(username__iexact=value).exclude(
                    pk=request.user.pk
                ).exists():
                    form.add_error('username', 'Este nome de usuário já existe.')
                else:
                    request.user.username = value
                    request.user.usernameinsensitive = value.upper()
                    request.user.save(update_fields=['username', 'usernameinsensitive'])
                    return logout(request)
            else:
                request.user.name = value
                request.user.save(update_fields=['name'])
                return redirect('/')
        else:
            messages.error(request, 'Verifique os dados informados.')
    else:
        form = ChangeUsername() if args else ChangeName()
    template = 'change/changeUsername.html' if args else 'change/changeName.html'
    return render(request, template, {'form': form})


@login_required(login_url='/login')
def changeUsername(request):
    return changeName(request, True)


def changePass(request):
    reset_user_id = request.session.get('password_reset_user_id')
    if reset_user_id:
        user = Usuario.objects.filter(pk=reset_user_id).first()
    elif request.user.is_authenticated:
        user = request.user
    else:
        return redirect('/login')
    if user is None:
        request.session.pop('password_reset_user_id', None)
        return redirect('/login')

    if request.method == 'POST':
        form = ChangePass(request.POST)
        if form.is_valid():
            if form.cleaned_data['senha'] != form.cleaned_data['confirme_sua_senha']:
                form.add_error('confirme_sua_senha', 'As senhas não são identicas.')
            elif len(form.cleaned_data['senha']) < 5:
                form.add_error('senha', 'A senha precisa ter no minimo 5 caracteres.')
            else:
                user.password = make_password(form.cleaned_data['senha'])
                user.save(update_fields=['password'])
                request.session.pop('password_reset_user_id', None)
                return logout(request)
    else:
        form = ChangePass()
    return render(request, 'change/changePass.html', {'form': form})


def email(request, *args):
    try:
        user = (
            request.user if not args
            else Usuario.objects.get(email__iexact=args[0])
        )
    except Usuario.DoesNotExist:
        return None

    current_site = get_current_site(request)
    message = render_to_string('emailconfirmation/changepassword.html', {
        'user': user,
        'domain': current_site.domain,
        'uid': urlsafe_base64_encode(force_bytes(user.pk)),
        'token': account_activation_token.make_token(user),
    })
    EmailMessage(
        'Trocar senha do ETEWITTER.',
        message,
        to=[user.email],
    ).send()
    return HttpResponse(
        'Por favor, clique no link enviado em seu email para mudar de senha'
    )
