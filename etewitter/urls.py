
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
from search import views

app_name='main'

urlpatterns = [
    path('', include("main.urls")),
    path('like/',include("main.urls")),
    path('likereply/',include("main.urls")),
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
    path('search/', include('search.urls')),
    path('<str:username>/',include('userprofile.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
