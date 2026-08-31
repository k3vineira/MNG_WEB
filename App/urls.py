# Si tus archivos se llaman views.py dentro de cada carpeta:
from .views.actividades.views import *
from .views.blog.views import *
from .views.categoria.views import *
from .views.paquete.views import *
from .views.pqrs.views import *
from .views.reserva.views import *
from .views.tarifa.views import *
from .views.temporada.views import *

from django.urls import path

urlpatterns = [

    path('nuestros-destinos/', destinos, name='destinos'),

    # categorias
    path('categorias/', CategoriaListView.as_view(), name='listar_categorias'),
    path('categorias/nueva/', CategoriaCreateView.as_view(), name='crear_categoria'),
    path('categorias/editar/<int:pk>/', CategoriaUpdateView.as_view(), name='editar_categoria'),
    path('categorias/eliminar/<int:pk>/', CategoriaDeleteView.as_view(), name='eliminar_categoria'),

    # actividades
    path('actividades/', ActividadesListView.as_view(), name='listar_actividades'),
    path('actividades/nueva/', ActividadesCreateView.as_view(), name='crear_actividad'),
    path('actividades/editar/<int:pk>/', ActividadesUpdateView.as_view(), name='editar_actividad'),
    path('actividades/eliminar/<int:pk>/', ActividadesDeleteView.as_view(), name='eliminar_actividad'),

    # paquetes
    path('paquetes/', PaqueteListView.as_view(), name='listar_paquetes'),
    path('paquetes/nuevo/', PaqueteCreateView.as_view(), name='crear_paquete'),
    path('paquetes/editar/<int:pk>/', PaqueteUpdateView.as_view(), name='editar_paquete'),
    path('paquetes/eliminar/<int:pk>/', PaqueteDeleteView.as_view(), name='eliminar_paquete'),

    # temporadas
    path('temporadas/', TemporadaListView.as_view(), name='listar_temporadas'),
    path('temporadas/nueva/', TemporadaCreateView.as_view(), name='crear_temporada'),
    path('temporadas/editar/<int:pk>/', TemporadaUpdateView.as_view(), name='editar_temporada'),

    # tarifas
    path('tarifas/', TarifaListView.as_view(), name='listar_tarifas'),
    path('tarifas/crear/', TarifaCreateView.as_view(), name='crear_tarifa'),
    path('tarifas/editar/<int:pk>/', TarifaUpdateView.as_view(), name='editar_tarifa'),

    # PQRS
    path('gestion/pqrs/', PQRSListView.as_view(), name='listar_pqrs'),
    path('gestion/pqrs/contestar/<int:pqrs_id>/', contestar_pqrs, name='contestar_pqrs'),
    path('mis_pqrs/', mis_pqrs_view, name='mis_pqrs'),
    path('pqrs/guardar/', guardar_pqrs, name='guardar_pqrs'),
    path('pqrs/', pqrs, name='pqrs'),

    # BLOG
    path('gestion/blog/', BlogListView.as_view(), name='listar_blog'),
    path('gestion/blog/nuevo/', BlogCreateView.as_view(), name='crear_blog'),
    path('gestion/blog/editar/<int:pk>/', BlogUpdateView.as_view(), name='editar_blog'),
    path('gestion/blog/eliminar/<int:pk>/', BlogDeleteView.as_view(), name='eliminar_blog'),
    path('blog/', blog, name='blog'),
    path('blog/<int:id>/', detalle_blog, name='detalle_blog'),

]