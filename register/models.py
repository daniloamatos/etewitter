from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
from django.contrib.auth.hashers import PBKDF2PasswordHasher
from django.core.exceptions import ValidationError
from datetime import datetime
import random
import os


def image_path(instance, filename):
    file_extension = os.path.splitext(filename)
    chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890'
    randomstr = ''.join((random.choice(chars)) for x in range(10))
    randomstr2 = ''.join((random.choice(chars)) for x in range(20))
    _now = datetime.now()

    return '{instance.id}/{day}/{month}/{year}/{randomstring}/{randomstring2}{ext}'.format(
        instance = instance, randomstring=randomstr, randomstring2=randomstr2,ext=file_extension[1],
        day=_now.strftime('%d'), month=_now.strftime('%m'), year=_now.strftime('%Y'))



class MyPBKDF2PasswordHasher(PBKDF2PasswordHasher):
    iterations = PBKDF2PasswordHasher.iterations * 1

class Usuario(AbstractUser):
    def validate_profilepic_size(value):
        filesize= value.size
        if filesize > 50*1024*1024:
            raise ValidationError("O tamanho máximo da foto de perfil é 50MB")
        else:
            return value


    def validate_banner_size(value):
        filesize= value.size
        if filesize > 50*1024*1024:
            raise ValidationError("O tamanho máximo da foto de capa é 50MB")
        else:
            return value

    validateSize = RegexValidator(regex='^.{4,25}$', message='O tamanho do nome tem que ser entre 4 e 25',  code='invalid_size')
    validateCharacters = RegexValidator(regex='^[a-zA-Z0-9]*$', message='Somente caracteres alfanuméricos são permitidos.', code='invalid_characters')
    username = models.CharField(validators=[validateSize, validateCharacters], max_length=25, unique=True, verbose_name="Nome de usuário")
    usernameinsensitive = models.CharField(max_length=25, unique=True, verbose_name="Nome de usuário")
    email = models.EmailField(unique=True)
    name = models.CharField(validators=[validateSize], max_length=25, verbose_name="Nome")
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'password']
    date_of_birth = models.DateTimeField(null=True,blank=True, verbose_name='Data de aniversário')
    date_of_creation = models.DateTimeField(default=datetime.now, blank=True)
    profilepic = models.ImageField(default="default/default_profile_400x400.png", blank=True, upload_to =image_path, verbose_name="Foto de perfil", validators=[validate_profilepic_size])
    bannerpic = models.ImageField(default="default/default.banner.jpg",blank=True, upload_to =image_path, verbose_name="Foto de capa", validators=[validate_banner_size])
    bio = models.CharField(blank=True, max_length=50, verbose_name="Sobre")
    followers = models.IntegerField(default=0)
    following = models.IntegerField(default=0)
    tweetsNumber = models.IntegerField(default=0)
    isAuthenticated = models.BooleanField(default=False)

    def get_posts_no(self):
        return self.posts.all().count()

    def get_all_authors_posts(self):
        return self.posts.all()

    """def get_likes_received(self):
        posts = self.posts.all()
        total_liked = 0
        for item in posts:
            total_liked += item.likes.all().count()
        return total_liked"""


           





