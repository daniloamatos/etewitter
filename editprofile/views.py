
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.templatetags.static import static
from .forms import userForm

DEFAULT_PROFILE_IMAGE = ""
DEFAULT_BANNER_IMAGE = ""
LEGACY_DEFAULT_PROFILE_IMAGE = "default/default_profile_400x400.png"
LEGACY_DEFAULT_BANNER_IMAGE = "default/default.banner.jpg"


def _normalize_image_name(value):
    if value in (None, ""):
        return ""
    if value in (LEGACY_DEFAULT_PROFILE_IMAGE, LEGACY_DEFAULT_BANNER_IMAGE):
        return ""
    return value


@login_required(login_url='/login')
def editprofile(request):
    user = request.user
    setDefaultPictures(user)
    if request.method == 'POST':
        form = userForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            old_profile = _normalize_image_name(getattr(user.profilepic, 'name', None))
            old_banner = _normalize_image_name(getattr(user.bannerpic, 'name', None))
            if "profilepic-clear" in request.POST and "profilepic" not in request.FILES:
                user.profilepic = DEFAULT_PROFILE_IMAGE
            if "bannerpic-clear" in request.POST and "bannerpic" not in request.FILES:
                user.bannerpic = DEFAULT_BANNER_IMAGE
            form.save()
            new_profile = _normalize_image_name(getattr(user.profilepic, 'name', None))
            new_banner = _normalize_image_name(getattr(user.bannerpic, 'name', None))
            if old_profile and old_profile != new_profile and old_profile not in (LEGACY_DEFAULT_PROFILE_IMAGE, LEGACY_DEFAULT_BANNER_IMAGE):
                if user.profilepic.storage.exists(old_profile):
                    user.profilepic.storage.delete(old_profile)
            if old_banner and old_banner != new_banner and old_banner not in (LEGACY_DEFAULT_PROFILE_IMAGE, LEGACY_DEFAULT_BANNER_IMAGE):
                if user.bannerpic.storage.exists(old_banner):
                    user.bannerpic.storage.delete(old_banner)
            return redirect("/editprofile")
    else:
        form = userForm(instance=user)
    return render(request, 'upload/upload.html', {
        'form': form,
        'default_profile_url': static('images/default-profile.svg'),
        'default_banner_url': static('images/default-banner.svg'),
    })


def setDefaultPictures(user):
    if not user.profilepic or user.profilepic.name in (LEGACY_DEFAULT_PROFILE_IMAGE, LEGACY_DEFAULT_BANNER_IMAGE):
        user.profilepic = DEFAULT_PROFILE_IMAGE
        user.save(update_fields=['profilepic'])
    if not user.bannerpic or user.bannerpic.name in (LEGACY_DEFAULT_PROFILE_IMAGE, LEGACY_DEFAULT_BANNER_IMAGE):
        user.bannerpic = DEFAULT_BANNER_IMAGE
        user.save(update_fields=['bannerpic'])