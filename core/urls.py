from django.contrib import admin
from django.urls import path, include
<<<<<<< HEAD

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('App.urls')),
=======
from App import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("App.urls"))
>>>>>>> 59a3ebe372eb455308020e845a9560af7bb44377
]
