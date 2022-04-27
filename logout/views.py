from django.shortcuts import redirect
# Create your views here.

def logout(request):
    request.user.is_authenticated = False
    return redirect('/index')
    