from django.contrib.auth.forms import UserCreationForm
from .models import Usuario
from django import forms
from django.utils.translation import gettext_lazy as _

class RegisterForm(UserCreationForm):
    password1 = forms.CharField(
        label=_("Senha"),
        widget=forms.PasswordInput(attrs={'class': 'form-controlss', 'id': 'inputPassword1', 'type':'password', 'style':"width:350px;height:50px;"}),
    )
    password2 = forms.CharField(
        label=_("Confirme a Senha"),
        widget=forms.PasswordInput(attrs={'class': 'form-controlss', 'id': 'inputPassword2', 'type':'password', 'style':"width:350px;height:50px;"}),
    )
    
    class Meta:
        model = Usuario
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-controlss', 'id': 'name', 'type':'name', 'style':"width:350px;height:50px;"}),
            'email': forms.TextInput(attrs={'class': 'form-controlss', 'id': 'email', 'type':'name', 'style':"width:350px;height:50px;"}),
        }

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if len(username) < 4:
            raise forms.ValidationError(_('O nome de usuário precisa ter pelo menos 4 caracteres.'))
        if len(username) > 25:
            raise forms.ValidationError(_('O nome de usuário pode ter no máximo 25 caracteres.'))
        if not username.isalnum():
            raise forms.ValidationError(_('O nome de usuário deve conter apenas letras e números.'))
        return username

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(_('Este e-mail já está cadastrado.'))
        return email

    def clean_password1(self):
        password = self.cleaned_data.get('password1', '')
        if len(password) < 5:
            raise forms.ValidationError(_('A senha precisa ter pelo menos 5 caracteres.'))
        return password
