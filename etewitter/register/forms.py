from django.contrib.auth.forms import UserCreationForm
from .models import Usuario
from django import forms

class RegisterForm(UserCreationForm):
    password1 = forms.CharField(
        label="Senha",
        widget=forms.PasswordInput(attrs={'class': 'form-controlss', 'id': 'inputPassword1', 'type':'password', 'style':"width:350px;height:50px;"}),
    )
    password2 = forms.CharField(
        label="Confirme a Senha",
        widget=forms.PasswordInput(attrs={'class': 'form-controlss', 'id': 'inputPassword2', 'type':'password', 'style':"width:350px;height:50px;"}),
    )
    
    class Meta:
        model = Usuario
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-controlss', 'id': 'name', 'type':'name', 'style':"width:350px;height:50px;"}),
            'email': forms.TextInput(attrs={'class': 'form-controlss', 'id': 'email', 'type':'name', 'style':"width:350px;height:50px;"}),
        }

