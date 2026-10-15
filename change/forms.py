from django import forms
from django.core.validators import RegexValidator

from register.models import Usuario


class ChangeName(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['name']


class ChangePass(forms.Form):
    senha = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Coloque a nova senha',
                'class': 'form-controlss',
                'id': 'inputPassword1',
                'type': 'password',
                'style': 'width:350px;height:50px;',
            }
        )
    )
    confirme_sua_senha = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                'placeholder': 'Confirme sua senha',
                'class': 'form-controlss',
                'id': 'inputPassword2',
                'type': 'password',
                'style': 'width:350px;height:50px;',
            }
        )
    )


class ChangeUsername(forms.Form):
    username = forms.CharField(
        min_length=4,
        max_length=25,
        validators=[
            RegexValidator(
                regex=r'^[a-zA-Z0-9]+$',
                message='Somente caracteres alfanuméricos são permitidos.',
            )
        ],
    )
