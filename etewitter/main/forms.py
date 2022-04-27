from django.db import models
from .models import Tweet
from django import forms

class tweetForm(forms.ModelForm):
    class Meta:
        model = Tweet
        fields = ['tweet',]

