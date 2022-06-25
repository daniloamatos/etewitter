import django
django.setup()
from django.db import models

class Message(models.Model):
    message = models.CharField(max_length=255)
    class Meta:
        app_label = 'mywebsite.chat'
