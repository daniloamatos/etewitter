
from django.shortcuts import render,  redirect
from django.contrib import messages
from django.contrib.auth import login as auth_login
from .models import Usuario
from .forms import RegisterForm
from .lookups import username_exists

def register(request):
    if request.user.is_authenticated:
        return redirect('/')
    else:
        if request.method == "POST":
            form = RegisterForm(request.POST)
            if form.is_valid() and username_exists(form.cleaned_data['username']):
                form.add_error('username', 'Este nome de usuário já está cadastrado.')
            if form.is_valid():
                t = form.save(commit=False)
                t.is_active = True
                t.name = form.cleaned_data['username']
                t.usernameinsensitive = form.cleaned_data['username'].upper()
                t.save()
                auth_login(request, t, backend='login.authenticate.authentication')
                return redirect("/")
            if not form.is_valid():
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f'{form.fields[field].label}: {error}')
        else:
            form = RegisterForm()
        return render(request, "register/register.html", {"form": form})
