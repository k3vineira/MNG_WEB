from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from django.views.generic.base import RedirectView
from django.templatetags.static import static as static_url

urlpatterns = [
    path('favicon.ico', RedirectView.as_view(url=static_url('img/monagua_log.ico'), permanent=True)),
    path('', include('App.urls')),
    path('admin/', admin.site.urls),
    path('autenticacion/', include('autenticacion.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

