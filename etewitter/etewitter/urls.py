"""etewitter URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from register import views as vr
from logout import views as vlogout
from login import views as vlogin
from validations import views as vemailconf
from change import views as vchange
from django.conf import settings
from django.conf.urls.static import static
from editprofile import views as veditprofile
from userprofile import views as vuserprofile

app_name='main'

urlpatterns = [
    path('', include("main.urls")),
    #path('tweet/',include("main.urls")),
    path("editprofile/", veditprofile.editprofile, name="editprofile"),
    path('register/', vr.register, name="register"),
    path('changename/', vchange.changeName, name="changeName"),
    path('changeusername/', vchange.changeUsername, name="changeUsername"),
    path('login/', vlogin.login, name='login'),
    path('logout/', vlogout.logout, name='logout'),
    path('admin/', admin.site.urls),
    path('activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/', vemailconf.activate, name='activate'),
    path('changepassword/', vchange.changePass, name="changePass"),
    path('confirmChange/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/', vemailconf.confirmChange, name="confirmChange"),
    path('<str:username>/',vuserprofile.userprofile, name="userprofile"),
    path('<str:username>/like/', vuserprofile.like, name="like"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
