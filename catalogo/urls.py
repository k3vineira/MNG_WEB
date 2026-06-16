from django.urls import path
from . import views


urlpatterns = [

    path('nuestros-destinos/', views.destinos, name='destinos'),

    # categorias
    path('categorias/', views.CategoriaListView.as_view(),
         name='listar_categorias'),
    path('categorias/nueva/', views.CategoriaCreateView.as_view(),
         name='crear_categoria'),
    path('categorias/editar/<int:pk>/',
         views.CategoriaUpdateView.as_view(), name='editar_categoria'),
    path('categorias/eliminar/<int:pk>/',
         views.CategoriaDeleteView.as_view(), name='eliminar_categoria'),

    # actividades
    path('actividades/', views.ActividadesListView.as_view(),
         name='listar_actividades'),
    path('actividades/nueva/', views.ActividadesCreateView.as_view(),
         name='crear_actividad'),
    path('actividades/editar/<int:pk>/',
         views.ActividadesUpdateView.as_view(), name='editar_actividad'),
    path('actividades/eliminar/<int:pk>/',
         views.ActividadesDeleteView.as_view(), name='eliminar_actividad'),

    # paquetes
    path('paquetes/', views.PaqueteListView.as_view(), name='listar_paquetes'),
    path('paquetes/nuevo/', views.PaqueteCreateView.as_view(), name='crear_paquete'),
    path('paquetes/editar/<int:pk>/',
         views.PaqueteUpdateView.as_view(), name='editar_paquete'),
    path('paquetes/eliminar/<int:pk>/',
         views.PaqueteDeleteView.as_view(), name='eliminar_paquete'),


    # temporadas
    path('temporadas/', views.TemporadaListView.as_view(),
         name='listar_temporadas'),
    path('temporadas/nueva/', views.TemporadaCreateView.as_view(),
         name='crear_temporada'),
    path('temporadas/editar/<int:pk>/',
         views.TemporadaUpdateView.as_view(), name='editar_temporada'),

    # tarifas
    path('tarifas/', views.TarifaListView.as_view(), name='listar_tarifas'),
    path('tarifas/crear/', views.TarifaCreateView.as_view(), name='crear_tarifa'),
    path('tarifas/editar/<int:pk>/',
         views.TarifaUpdateView.as_view(), name='editar_tarifa'),
]
