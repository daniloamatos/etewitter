
from django.shortcuts import render,  redirect
from django.contrib import messages
from django.contrib.auth import login as auth_login
from .models import Usuario
from .forms import RegisterForm
# Mantidos para preservar o fluxo antigo de confirmação por e-mail:
# from django.core.mail import EmailMessage
# from django.template.loader import render_to_string
# from django.contrib.sites.shortcuts import get_current_site
# from django.utils.http import urlsafe_base64_encode
# from django.utils.encoding import force_bytes
# from .tokens import account_activation_token
from check.views import checkIfUsernameExists, checkIfEmailExists

def register(request):
    if request.user.is_authenticated:
        return redirect('/')
    else:
        if request.method == "POST":
            form = RegisterForm(request.POST)
            if form.is_valid() and checkIfUsernameExists(request, form.cleaned_data['username']):
                form.add_error('username', 'Este nome de usuário já está cadastrado.')
            if form.is_valid():
                t = form.save(commit=False)
                t.is_active = True
                t.name = form.cleaned_data['username']
                t.usernameinsensitive = form.cleaned_data['username'].upper()
                t.save()
                auth_login(request, t, backend='login.authenticate.authentication')


                # email confirmation || 
                # current_site = get_current_site(request)
                # mail_subject = 'Ative sua conta no ETEWITTER.'
                # message = render_to_string('emailconfirmation/acc_active_email.html', {
                #     'user': t, 'domain': current_site.domain,
                #     'uid': urlsafe_base64_encode(force_bytes(t.pk)),
                #     'token': account_activation_token.make_token(t),
                # })
                # EmailMessage(mail_subject, message, to=[form.cleaned_data['email']]).send()

                return redirect("/")
            if not form.is_valid():
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{form.fields[field].label}: {error}')
        else:
            form = RegisterForm()
        return render(request, "register/register.html", {"form": form})
