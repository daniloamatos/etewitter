from tabnanny import verbose
from django import forms, template
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import Usuario
from django.contrib.auth.views import LoginView
from django.db import models

class RegisterForm(UserCreationForm):
    class Meta:
        model = Usuario
        fields = ['username', 'email', 'password1', 'password2']

class ChangeName(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['name']

class ChangePass(forms.Form):
        senha = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Coloque a nova senha'}))
        confirme_sua_senha = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirme sua senha'}))
        fields = ['password', 'password2']


class LoginForm(forms.Form):
    usuario = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Usuário'}))
    senha = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Senha'}))
    fields = ['usuario', 'password']
   