from django.db import models
from register.models import Usuario
from django.core.exceptions import ValidationError
from django.contrib.auth.models import User
from register.models import image_path

def validate_profilepic_size(value):
    filesize= value.size
    if filesize > 4110000:
        raise ValidationError("The maximum profilepic size that can be uploaded is 4MB")
    else:
        return value

class profilePic(models.Model):
    profilepic = models.ImageField(blank=True, upload_to=image_path, verbose_name="Foto de perfil", validators=[validate_profilepic_size])
