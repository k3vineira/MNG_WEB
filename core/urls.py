from django.contrib import admin
from django.urls import path, include
from .views import inicio
from comunidad.views import resenas_view


urlpatterns = [
    path('admin/', admin.site.urls),
    path('usuarios/', include('usuarios.urls')),
    path('comunidad/', include('comunidad.urls')),
    path('reservas/', include('reservas.urls')),
    path('', inicio, name='inicio'),
    path('pagos/', include('pagos.urls')),
    path('mis-comentarios/', resenas_view, name='comentarios'),
    path('promociones/', include('promociones.urls')),
]
