from getpass import getuser
from django.http import HttpResponse
from django.shortcuts import render, redirect
from .forms import userForm
import os
from django.contrib.auth.decorators import login_required
  
# Create your views here.
@login_required(login_url="/login")
def editprofile(request):
    defaultProfile = "default/default_profile_400x400.png"
    defaultBanner = "default/default.banner.jpg"
    user = request.user
    setDefaultPictures(user, defaultProfile, defaultBanner)
    if request.method == 'POST':
        form = userForm(request.POST, request.FILES, instance=user)
        if 'profilepic' in request.FILES and user.profilepic != defaultProfile or "profilepic-clear" in request.POST and user.profilepic != defaultProfile:
            user.profilepic.delete(save=True)
        if 'bannerpic' in request.FILES and user.bannerpic !=  defaultBanner or "bannerpic-clear" in request.POST and user.bannerpic != defaultBanner:
            user.bannerpic.delete(save=True)
        if form.is_valid():
            form.save()
            deleteFolders()
            return redirect("/editprofile")
    else:
        form = userForm(instance=user)
    return render(request, 'upload/upload.html', {'form' : form})
  

def setDefaultPictures(user, defaultProfile, defaultBanner):
    if not user.profilepic:
        user.profilepic = defaultProfile
        user.save()
    if not user.bannerpic:
        user.bannerpic = "default/default.banner.jpg"
        user.save()

def deleteFolders():
    root = "/home/danilo/Desktop/etewitter/etewitter/uploads"
    folders = sorted(list(os.walk(root))[1:],reverse=True)
    for folder in folders:
        try:
            os.rmdir(folder[0])
        except OSError as error: 
            pass