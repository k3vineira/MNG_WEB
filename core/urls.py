from django.contrib import admin
from django.urls import path, include
from .views import inicio
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('admin/', admin.site.urls),
    path('usuarios/', include('usuarios.urls')),
    path('catalogo/', include('catalogo.urls')),
    path('reservas/', include('reservas.urls')),
    path('comunidad/', include('comunidad.urls')),
    path('', inicio, name='inicio'),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)