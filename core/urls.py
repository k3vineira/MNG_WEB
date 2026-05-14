from django.contrib import admin
from django.urls import path, include
from .views import inicio



urlpatterns = [
    path('admin/', admin.site.urls),
    path('usuarios/', include('usuarios.urls')),
    path('catalogo/', include('catalogo.urls')),
    path('reservas/', include('reservas.urls')),
    path('comunidad/', include('comunidad.urls')),
    path('', inicio, name='inicio'),
]
