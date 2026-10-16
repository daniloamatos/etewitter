from .models import Usuario


def username_exists(username):
    return Usuario.objects.filter(username__iexact=username).exists()
