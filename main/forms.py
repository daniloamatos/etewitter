from django.db import models
from .models import Tweet, Replys
from .image_utils import IMAGE_ACCEPT_ATTRIBUTE
from django import forms
from django.utils.translation import gettext_lazy as _

class tweetForm(forms.ModelForm):
    class Meta:
        model = Tweet
        fields = ['tweet','image']
        labels = {
            'tweet':'',
            'image':'',
        }
        widgets = {
            'tweet': forms.TextInput(attrs={'placeholder': _('O que está acontecendo?'), 'id': 'tweetBox', 'name': 'tweet', 'type':'text'}),
            'image': forms.ClearableFileInput(attrs={'accept': IMAGE_ACCEPT_ATTRIBUTE}),
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
            'body': forms.TextInput(attrs={'placeholder': _('Tweete sua resposta'), 'id': 'tweetBox', 'name': 'tweet', 'type':'text'}),
            'image': forms.ClearableFileInput(attrs={'accept': IMAGE_ACCEPT_ATTRIBUTE}),
        }

