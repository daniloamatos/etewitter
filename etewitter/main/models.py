from django.db import models
from datetime import datetime
#from register.models import Usuario


class Tweet(models.Model):
    tweet = models.CharField(blank=False, max_length=280)
    tweetAuthor = models.IntegerField(blank=False)
    likes = models.IntegerField(blank=True, default=0)
    #replys = models.ForeignKey(?, on_delete=models.CASCADE)
    publishDate = models.DateTimeField(auto_now_add=True, blank=True)