from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login as authLogin
from change.forms import  ChangePass
from django.utils.http import  urlsafe_base64_decode
from django.utils.encoding import force_str
from register.tokens import account_activation_token
from register.models import Usuario



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
        return render(request, "change/changePass.html", {"form":form})
    else:
        return HttpResponse('Algo deu errado!')

