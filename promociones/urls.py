from django.urls import path
from . import views

urlpatterns = [
    path('gestion/', views.promociones_gestion, name='promociones_gestion'),
    path('guardar/', views.guardar_promocion, name='guardar_promocion'),
    path('eliminar/<int:id>/', views.eliminar_promocion, name='eliminar_promocion'),
]