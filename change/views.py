from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib import messages
from register.models import Usuario
from django.contrib.auth.decorators import login_required
from .forms import ChangeName, ChangePass
from django.contrib.auth.hashers import make_password
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from register.tokens import account_activation_token
from logout.views import logout

# Create your views here.
@login_required(login_url='/login')
def changeName(request, *args):
    if request.method == "POST":
        current_user = request.user
        form = ChangeName(request.POST)
        if len(form.data['name']) < 4 or len(form.data['name']) > 25:
                messages.error(request, 'O tamanho do nome tem que ser entre 4 e 25.')
        else:
            t = Usuario.objects.get(id=current_user.id)
            if not args:
                t.name = request.POST.get('name')
                t.save()
                return redirect("/")
            else:
                if form.is_valid():
                    t.username = request.POST.get('name')
                    t.save()
                    logout(request)
                else:
                    messages.error(request, 'Somente caracteres alfanuméricos são permitidos no nome de usuario.')
    else:
        form = ChangeName()
    return render(request, "change/changeName.html", {"form":form})

@login_required(login_url='/login')
def changeUsername(request):
    if request.method == "POST":
        form = ChangeName(request.POST)
        username = True
        return changeName(request, username)
    else:
        form = ChangeName()
    return render(request, "change/changeUsername.html", {"form":form})

@login_required(login_url='/login')
def changePass(request):
    if request.method == "POST":
        current_user = request.user
        form = ChangePass(request.POST)
        if request.POST['senha'] != request.POST['confirme_sua_senha']:
            messages.error(request, 'As senhas não são identicas.')
        elif len(form.data['senha']) <8:
            messages.error(request, 'A senha precisa ter no minimo 8 caracteres.')
        else:
            current_user.password = make_password(request.POST['senha'])
            current_user.save()
            return logout(request) 
    else:
        form = ChangePass()
        current_user = request.user
        t = Usuario.objects.get(id=current_user.id)
        current_site = get_current_site(request)
        mail_subject = 'Trocar senha do ETEWITTER.'
        message = render_to_string('emailconfirmation/changepassword.html', {
            'user': t,
            'domain': current_site.domain,
            'uid':urlsafe_base64_encode(force_bytes(t.pk)),
            'token':account_activation_token.make_token(t),
        })
        to_email = Usuario.objects.values_list("email").filter(email=current_user.email).first()
        print(to_email[0])
        email = EmailMessage(
                    mail_subject, message, to=[to_email[0]]
        )
        email.send()
        return HttpResponse('Por favor, clique no link enviado em seu email para mudar de senha')
    return render(request, "change/changePass.html",{'form':form})