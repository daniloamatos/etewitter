from django.urls import path
from . import views

urlpatterns = [
    path('',views.userprofile, name="userprofile"),
    path('like/', views.like, name="like"),
    path('status/reply', views.reply, name="reply"),
    path('status/<str:random>',views.requesttweet, name="requesttweet"),

]
