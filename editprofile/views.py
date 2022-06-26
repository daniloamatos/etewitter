
from django.shortcuts import render, redirect
from .forms import userForm

from django.shortcuts import render, redirect
import cloudinary
import cloudinary.uploader
import cloudinary.api

def editprofile(request):
    defaultProfile = "default/default_profile_400x400.png"
    defaultBanner = "default/default.banner.jpg"
    user = request.user
    setDefaultPictures(user, defaultProfile, defaultBanner)
    if request.method == 'POST':
        form = userForm(request.POST, request.FILES, instance=user)
        if 'profilepic' in request.FILES and user.profilepic != defaultProfile or "profilepic-clear" in request.POST and user.profilepic != defaultProfile:
            cloudinary.uploader.destroy(str(user.profilepic))
            user.profilepic.delete(save=True)
        if 'bannerpic' in request.FILES and user.bannerpic !=  defaultBanner or "bannerpic-clear" in request.POST and user.bannerpic != defaultBanner:
            cloudinary.uploader.destroy(str(user.bannerpic))
            user.bannerpic.delete(save=True)
        if form.is_valid():
            form.save()
            return redirect("/editprofile")
    else:
        form = userForm(instance=user)
    return render(request, 'upload/upload.html', {'form' : form})
  

def setDefaultPictures(user, defaultProfile, defaultBanner):
    if not user.profilepic:
        user.profilepic = defaultProfile
        user.save()
    if not user.bannerpic:
        user.bannerpic = defaultBanner
        user.save()