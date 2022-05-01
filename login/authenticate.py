from register.models import Usuario
from django.contrib.auth.backends import BaseBackend

class authentication(BaseBackend):
    def authenticateCustom(request, username=None, password=None):
            user = Usuario.objects.get(usernameinsensitive=username.upper())
            try:
                return user
            except:
                return None

    def get_user(user_id):
        try:
            return Usuario.objects.get(pk=user_id)
        except Usuario.DoesNotExist:
            return None

