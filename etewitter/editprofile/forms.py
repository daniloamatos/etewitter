from django import forms
from .models import *
  
class userForm(forms.ModelForm):
    class Meta:
        model = Usuario
        fields = ['profilepic', 'bannerpic', 'bio']