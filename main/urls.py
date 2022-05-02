from django.urls import path, include
from . import views
from userprofile import views as vu

urlpatterns = [
    path('', views.home, name='home'),
    path('index/', views.index, name="index"),
    path("like/", vu.like, name="like"),
    path('likereply/', vu.likereply, name="likereply"),
    
]
