from django.db import models
from register.models import Usuario
from django.core.validators import FileExtensionValidator
from datetime import datetime
import random
import os


def image_path(instance, filename):
    file_extension = os.path.splitext(filename)
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890'
    randomstr = ''.join((random.choice(chars)) for x in range(10))
    randomstr2 = ''.join((random.choice(chars)) for x in range(20))
    _now = datetime.now()

    return '{instance.tweetAuthor.id}/{day}/{month}/{year}/{randomstring}/{randomstring2}{ext}'.format(
        instance = instance, randomstring=randomstr, randomstring2=randomstr2,ext=file_extension[1],
        day=_now.strftime('%d'), month=_now.strftime('%m'), year=_now.strftime('%Y'))

def image_path2(instance, filename):
    file_extension = os.path.splitext(filename)
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890'
    randomstr = ''.join((random.choice(chars)) for x in range(10))
    randomstr2 = ''.join((random.choice(chars)) for x in range(20))
    _now = datetime.now()

    return '{instance.user.id}/{day}/{month}/{year}/{randomstring}/{randomstring2}{ext}'.format(
        instance = instance, randomstring=randomstr, randomstring2=randomstr2,ext=file_extension[1],
        day=_now.strftime('%d'), month=_now.strftime('%m'), year=_now.strftime('%Y'))

class Tweet(models.Model):
    tweet = models.CharField(blank=True, max_length=280)
    tweetAuthor = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="posts")
    image = models.ImageField(upload_to=image_path, validators=[FileExtensionValidator(['png', 'jpg', 'jpeg', 'gif'])], blank=True)
    likes = models.ManyToManyField(Usuario, blank=True, related_name="likes")
    publishDate = models.DateTimeField(auto_now_add=True, blank=True)
    tweetLink = models.CharField(blank=True, max_length=999)

    def __str__(self):
        return str(self.tweet[:20])

    def num_likes(self):
        return self.likes.all().count()

    def num_comments(self):
        return self.Replys_set.all.count()

class Replys(models.Model):
    user = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE)
    body = models.CharField(blank=True, max_length=280)
    image = models.ImageField(upload_to=image_path2, validators=[FileExtensionValidator(['png', 'jpg', 'jpeg', 'gif'])], blank=True)
    publishDate = models.DateTimeField(auto_now_add=True, blank=True)
    likes = models.ManyToManyField(Usuario, blank=True, related_name="replyLikes")
    replyLink = models.CharField(blank=True, max_length=999)


    def __str__(self):
        return str(self.pk)

    def num_likes(self):
        return self.likes.all().count()



LIKE_CHOICES = (
    ('Like', 'Like'),
    ('Unlike', 'Unlike'),
)

class Like(models.Model):
    user = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE)
    value = models.CharField(choices=LIKE_CHOICES, max_length=8)

    def __str__(self):
        return f'{self.user}--{self.tweet}--{self.value}'