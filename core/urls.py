from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    # Sitio público — único activo por ahora
    path('', include('catalogo.urls')),  # ← sin .public

    # Autenticación
    path('login/', include('django.contrib.auth.urls')),

    # TODO: descomentar cuando se creen los urls/ de cada app
    # path('registro/',              include('usuarios.urls.cliente')),
    # path('mi-cuenta/',             include('usuarios.urls.cliente')),
    # path('guia/',                  include('guias.urls.guia')),
    # path('dashboard/',             include('usuarios.urls.admin')),
    # path('mi-cuenta/reservas/',    include('reservas.urls.cliente')),
    # path('mi-cuenta/pagos/',       include('pagos.urls.cliente')),
    # path('mi-cuenta/comunidad/',   include('comunidad.urls.cliente')),
    # path('dashboard/catalogo/',    include('catalogo.urls.admin')),
    # path('dashboard/reservas/',    include('reservas.urls.admin')),
    # path('dashboard/pagos/',       include('pagos.urls.admin')),
    # path('dashboard/guias/',       include('guias.urls.admin')),
    # path('dashboard/promociones/', include('promociones.urls.admin')),
    # path('dashboard/comunidad/',   include('comunidad.urls.admin')),
    # path('asistente/',             include('asistente.urls')),
]
