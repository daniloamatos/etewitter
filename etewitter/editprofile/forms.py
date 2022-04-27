from django import forms
from register.models import Usuario
  
class userForm(forms.ModelForm):
    
    class Meta:
        model = Usuario
        fields = ['profilepic', 'bannerpic', 'bio', 'name']
