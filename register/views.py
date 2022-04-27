
from django.http import HttpResponse
from django.shortcuts import render,  redirect
from django.contrib import messages
from .models import Usuario
from .forms import RegisterForm
from django.contrib.auth.decorators import user_passes_test
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from .tokens import account_activation_token
from check.views import checkIfUsernameExists, checkIfEmailExists

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
                    messages.error(request, 'email ja utilizado')
            else:
                messages.error(request, 'usuário ja existe')
        else:
            messages.error(request, 'Digite informações validas.')
    else:
        form = RegisterForm()
        return render(request, "register/register.html", {"form":form})
    return redirect("/register")    
