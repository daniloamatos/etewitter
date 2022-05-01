
from django.http import HttpResponse
from django.shortcuts import render,  redirect
from django.contrib import messages
from .models import Usuario
from .forms import RegisterForm
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from .tokens import account_activation_token
from check.views import checkIfUsernameExists, checkIfEmailExists

def register(request):
    if str(request.user) != 'AnonymousUser':
        return redirect('/')
    else:
        if request.method == "POST":
            form = RegisterForm(request.POST)
            if len(form.data['username']) < 4 or len(form.data['username']) > 25:
                messages.error(request, 'O tamanho do nome tem que ser entre 4 e 25.')
            elif form.data['password1'] !=  form.data['password2']:
                messages.error(request, 'As senhas não são identicas.')
            elif len(form.data['password1']) <8:
                messages.error(request, 'A senha precisa ter no minimo 8 caracteres.')
            elif checkIfUsernameExists(request, request.POST['username'].upper()):
                messages.error(request, 'usuário ja existe')
            elif checkIfEmailExists(request, request.POST['email'].upper()):
                messages.error(request, 'email ja utilizado')
            elif form.is_valid():
                id = Usuario.objects.last().id + 1
                form.save()
                t = Usuario.objects.get(id=id)
                t.is_active = False
                t.name = request.POST.get('username')
                t.usernameinsensitive = request.POST.get('username').upper()
                t.save()
                current_site = get_current_site(request)
                mail_subject = 'Ative sua conta no ETEWITTER.'
                message = render_to_string('emailconfirmation/acc_active_email.html', {
                    'user': t,
                    'domain': current_site.domain,
                    'uid':urlsafe_base64_encode(force_bytes(t.pk)),
                    'token':account_activation_token.make_token(t),
                })
                to_email = form.cleaned_data.get('email')
                email = EmailMessage(
                            mail_subject, message, to=[to_email]
                )
                email.send()
                return HttpResponse('Por favor, confirme seu email para poder utilizar sua conta')
            else:
                messages.error(request, 'Somente caracteres alfanuméricos são permitidos no nome de usuario.')
        else:
            form = RegisterForm()
            return render(request, "register/register.html", {"form":form})
        return redirect("/register")    
