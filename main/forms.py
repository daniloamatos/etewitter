from django.db import models
from .models import Tweet
from django import forms

class tweetForm(forms.ModelForm):
    class Meta:
        model = Tweet
        fields = ['tweet','image']
        labels = {
            'tweet':'',
            'image':'',
        }
        widgets = {
            'tweet': forms.TextInput(attrs={'placeholder': 'O que está acontecendo?', 'id': 'tweetBox', 'name': 'tweet', 'type':'text'}),
        }

