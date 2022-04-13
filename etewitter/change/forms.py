
from django import forms
from register.models import Usuario

class ChangeName(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['name']

class ChangePass(forms.Form):
        senha = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Coloque a nova senha'}))
        confirme_sua_senha = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'Confirme sua senha'}))
        fields = ['password', 'password2']
   