
from django.http import Http404, request, HttpResponse, HttpResponseNotFound
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import Usuario
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as authLogin, authenticate
from .forms import ChangeName, RegisterForm, LoginForm, ChangePass
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth.decorators import user_passes_test
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from .tokens import account_activation_token



@user_passes_test(lambda u: not Usuario.is_authenticated, login_url='/')
def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            id = Usuario.objects.last().id + 1
            if checkIfUsernameExists(request, request.POST['username'].upper()) is False:
                if checkIfEmailExists(request, request.POST['email'].upper()) is  False:
                    form.save()
                    t = Usuario.objects.get(id=id)
                    t.is_active = False
                    t.name = request.POST.get('username')
                    t.save()
                    current_site = get_current_site(request)
                    mail_subject = 'Ative sua conta no ETEWITTER.'
                    message = render_to_string('register/acc_active_email.html', {
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
                    messages.error(request, 'email ja utilizado')
            else:
                messages.error(request, 'usuário ja existe')
        else:
            messages.error(request, 'Digite informações validas.')     
    else:
        form = RegisterForm()
    return render(request, "register/register.html", {"form":form})


@user_passes_test(lambda u: not Usuario.is_authenticated, login_url='/')
def login(request):
    form = LoginForm(request.POST)
    if request.method == "POST":
        if form.is_valid():
            username = request.POST['usuario']
            password = request.POST['senha']
            check = checkIfUsernameExists(request, username)
            if check is True:
                u = Usuario.objects.filter(username__iexact=username).first()
                if check_password(password, u.password):
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
        LoginForm()
    return render(request, "register/login.html", {"form":form})



@login_required(login_url='/login')
def changeName(request, *args):
    if request.method == "POST":
        current_user = request.user
        form = ChangeName(request.POST)
        if form.is_valid():
            t = Usuario.objects.get(id=current_user.id)
            if not args:
                t.name = request.POST.get('name')
                t.save()
                return redirect("/")
            else:
                t.username = request.POST.get('name')
                t.save()
                logout(request)
        else:
            messages.error(request, 'Digite um nome valido.')
    else:
        form = ChangeName()
    return render(request, "register/changeName.html", {"form":form})

@login_required(login_url='/login')
def changeUsername(request):
    if request.method == "POST":
        form = ChangeName(request.POST)
        username = True
        return changeName(request, username)
    else:
        form = ChangeName()
    return render(request, "register/changeUsername.html", {"form":form})

@login_required(login_url='/login')
def changePass(request):
    if request.method == "POST":
        current_user = request.user
        form = ChangePass(request.POST)
        if form.is_valid():
            current_user.password = make_password(request.POST['senha'])
            current_user.save()
            return logout(request)
    else:
        form = ChangePass()
        current_user = request.user
        t = Usuario.objects.get(id=current_user.id)
        current_site = get_current_site(request)
        mail_subject = 'Trocar senha do ETEWITTER.'
        message = render_to_string('register/changepassword.html', {
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
    return render(request, "register/changePass.html",{'form':form})

def checkIfUsernameExists(request, usernameUpper):
    check = Usuario.objects.filter(username__iexact=usernameUpper).first()
    if check is None:
        return False
    else:
        return True

def checkIfEmailExists(request, emailUpper):
    check = Usuario.objects.filter(email__iexact=emailUpper).first()
    if check is None:
        return False
    else:
        return True

def checkPassword(password):
    u = Usuario.objects.all().first()
    check = check_password(password, u.password)
    print(password, u.password)
    return check

@login_required(login_url='/login')
def logout(request):
    Usuario.is_authenticated = False
    return render(request,"register/logout.html", {})
    
def activate(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Usuario.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        authLogin(request, user)
        return HttpResponse('Obrigado por confirmar o email.Agora você pode fazer o <a href="/login">login</a> na sua conta.')
    else:
        return HttpResponse('Link de ativação é invalido')

@login_required(login_url='/login')
def confirmChange(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = Usuario.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        form = ChangePass()
        return render(request, "register/changePass.html", {"form":form})
    else:
        return HttpResponse('Algo deu errado!')
