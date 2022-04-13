
from django import forms
from django.contrib.auth.forms import UserCreationForm

class LoginForm(forms.Form):
    usuario = forms.CharField(widget=forms.TextInput(attrs={'placeholder': 'Usuário'}))
    senha = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Senha'}))
    fields = ['usuario', 'password']