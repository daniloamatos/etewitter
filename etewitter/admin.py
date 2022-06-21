from django.contrib import admin
from main.models import Tweet, Replys, Like, Message, Follower, SavedItems
from register.models import Usuario

admin.site.register(Usuario)
admin.site.register(Tweet)
admin.site.register(Replys)
admin.site.register(Like)
admin.site.register(Message)
admin.site.register(Follower)
admin.site.register(SavedItems)