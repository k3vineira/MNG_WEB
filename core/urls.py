from django.contrib import admin
from django.urls import path, include
from .views import inicio


urlpatterns = [
    path('admin/', admin.site.urls),
    path('usuarios/', include('usuarios.urls')),
    path('comunidad/', include('comunidad.urls')),
    path('reservas/', include('reservas.urls')),
    path('', inicio, name='inicio'),
]
