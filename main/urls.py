from django.urls import path, include, re_path
from . import views
from userprofile import views as vu

urlpatterns = [
    path('', views.home, name='home'),
    path('report/', views.report, name="report"),
    path('notifications/', views.notifications, name="notifications"),
    path('replies/<uuid:reply_id>/children/', views.reply_children, name='reply_children'),
    path('mention-suggestions/', views.mention_suggestions, name='mention_suggestions'),
    path('index/', views.index, name="index"),
    path("like/", vu.like, name="like"),
    path('likereply/', vu.likereply, name="likereply"),
    path('save/', vu.save, name="save"),
]
