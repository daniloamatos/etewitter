from django.db import models
from .models import Tweet, Replys
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
            'tweet': forms.TextInput(attrs={'placeholder': 'O que está acontecendo?', 'id': 'tweetBox', 'name': 'tweet', 'type':'text'})
        }

class replyForm(forms.ModelForm):
    class Meta:
        model = Replys
        fields = ['body','image']
        labels = {
            'body':'',
            'image':'',
        }
        widgets = {
            'body': forms.TextInput(attrs={'placeholder': 'Tweete sua resposta', 'id': 'tweetBox', 'name': 'tweet', 'type':'text'})
        }

