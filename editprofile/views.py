
from django.shortcuts import render, redirect
from .forms import userForm
import os
from PIL import Image
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
# Create your views here.
from django.db import connection

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
            if 'profilepic' in request.FILES:
                test = compressImg(user)
                user.profilepic.delete(save=True)
                user.profilepic = test
                form.save()
                deleteFolders()
                return redirect("/editprofile")
            else:
                setDefaultPictures(user, defaultProfile, defaultBanner)
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

def compressImg(user):
    im = Image.open(user.profilepic)
    rgb_im = im.convert('RGB')
    path = str(user.profilepic.path).split('/')
    test = path.pop()
    path = '/'.join(path)
    test = test.split('.')
    del test[-1]
    rgb_im.save(f"{path}/{test[0]}.jpeg", 'jpeg', quality=85, optimize=True)
    url = str(user.profilepic.url).split('/')
    del url[0]
    del url[0]
    url = '/'.join(url)
    url = url.split('.')
    del url[-1]
    return (f"{url[0]}.jpeg")
