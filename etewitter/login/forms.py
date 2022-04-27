
from django import forms
from django.contrib.auth.forms import UserCreationForm

class LoginForm(forms.Form):
    usuario = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Usuário', 'class': 'form-controlss', 'id': 'name', 'type':'name', 'style':"width:350px;height:50px;"}))
    senha = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Senha', 'class': 'form-controlss', 'id': 'inputPassword', 'type':'password', 'style':"width:350px;height:50px;"}))
    fields = ['usuario', 'password']
