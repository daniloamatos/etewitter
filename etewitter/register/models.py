from django.db import models
from django.contrib.auth.models import User, AbstractUser
from django.core.validators import RegexValidator
from django.contrib.auth.hashers import PBKDF2PasswordHasher

class MyPBKDF2PasswordHasher(PBKDF2PasswordHasher):
    iterations = PBKDF2PasswordHasher.iterations * 1

class Usuario(AbstractUser):
    validateName = RegexValidator(regex='^.{4,25}$', message='O tamanho do nome tem que ser entre 4 e 25')
    username = models.CharField(validators=[validateName], max_length=25, unique=True)
    email = models.EmailField(unique=True)
    name = models.CharField(validators=[validateName], max_length=25)
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email', 'password']
    is_authenticated = False