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
from django.http import request
from django.urls import path, include
from register import views as vr
from django.contrib.auth import logout
from django.conf import settings

app_name='main'

urlpatterns = [
    path('', include("main.urls")),
    path('register/', vr.register, name='register'),
    path('changename/', vr.changeName, name="changeName"),
    path('changeusername/', vr.changeUsername, name="changeUsername"),
    path('login/', vr.login, name="login"),
    path('logout/', vr.logout, name='logout'),
    path('admin/', admin.site.urls),
    path('', include("django.contrib.auth.urls")),
    path('activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/', vr.activate, name='activate'),
    path('changepassword/', vr.changePass, name="changePass"),
    path('confirmChange/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/', vr.confirmChange, name="confirmChange")
]
