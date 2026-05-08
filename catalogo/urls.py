from django.urls import path
from . import views

app_name = 'public'

urlpatterns = [
    path('', views.inicio, name='inicio'),
    # Se descomenta cuando se cree cada vista:
    # path('destinos/', views.destinos, name='destinos'),
    # path('paquetes/', views.paquetes, name='paquetes'),
    # path('paquetes/<int:pk>/', views.detalle_paquete, name='detalle_paquete'),
    # path('promociones/', views.promociones, name='promociones'),
    # path('blog/', views.blog, name='blog'),
    # path('blog/<int:pk>/', views.blog_detalle, name='blog_detalle'),
    # path('nosotros/', views.nosotros, name='nosotros'),
    # path('terminos/', views.terminos, name='terminos'),
]