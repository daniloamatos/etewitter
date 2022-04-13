
from register.models import Usuario
from django.contrib.auth.hashers import check_password

def checkIfUsernameExists(request, usernameUpper):
    check = Usuario.objects.filter(username__iexact=usernameUpper).first()
    if check is None:
        return False
    else:
        return True

def checkIfEmailExists(request, emailUpper):
    check = Usuario.objects.filter(email__iexact=emailUpper).first()
    if check is None:
        return False
    else:
        return True

def checkPassword(password):
    u = Usuario.objects.all().first()
    check = check_password(password, u.password)
    print(password, u.password)
    return check
