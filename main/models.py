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
    likec = models.IntegerField(default=0)
    publishDate = models.DateTimeField(auto_now_add=True, blank=True)
    tweetLink = models.CharField(blank=True, max_length=999)
    replysC = models.IntegerField(default=0)
    mentionlink = models.CharField(blank=True, max_length=999)

    def __str__(self):
        return str(self.tweet[:20])

    def num_likes(self):
        return self.likes.all().count()

class SavedItems(models.Model):
    user = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE)


class Replys(models.Model):
    user = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE)
    reply = models.ManyToManyField('self', blank = True)
    body = models.CharField(blank=True, max_length=280)
    image = models.ImageField(upload_to=image_path2, validators=[FileExtensionValidator(['png', 'jpg', 'jpeg', 'gif'])], blank=True)
    publishDate = models.DateTimeField(auto_now_add=True, blank=True)
    likes = models.ManyToManyField(Usuario, blank=True, related_name="likesr")
    likec = models.IntegerField(default=0)
    replyLink = models.CharField(blank=True, max_length=999)
    replysC = models.IntegerField(default=0)


    def __str__(self):
        return str(self.pk)



class Like(models.Model):
    user = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE)

    def __str__(self):
        return f'{self.user}--{self.tweet}--{self.value}'

class Follower(models.Model):
    follower = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="userToBeFollowed")
    following = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="userFollowing")
    
class Message(models.Model):
    sender = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="sender")
    receiver = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="receiver")
    body = models.CharField(blank=True, max_length=250)
    publishDate = models.DateTimeField(auto_now_add=True)

class Chat(models.Model):
    sender = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="senderC")
    receiver = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="receiverC")
    publishDate = models.DateTimeField(auto_now_add=True)

class Report(models.Model):
    tweet = models.ForeignKey(Tweet, on_delete=models.CASCADE)
    reason = models.CharField(blank=False, max_length=100)
    x9 = models.ForeignKey(Usuario, on_delete=models.CASCADE)

class Notification(models.Model):
    user = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name="notified")
    body = models.CharField(blank=False, max_length=250)
    linkzaocarai = models.CharField(blank=False, max_length=250)