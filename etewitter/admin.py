from django.contrib import admin
from main.models import Tweet, Replys, Like

admin.site.register(Tweet)
admin.site.register(Replys)
admin.site.register(Like)