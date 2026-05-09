# En cada app: urls/__init__.py  ← vacío
# urls/public.py o urls/cliente.py o urls/admin.py

from django.urls import path
from reservas import views   # o: from nombre_app import views

app_name = 'reservas'   # ← cambia por cada app

urlpatterns = [
     path('reservar/', views.reservas_view, name='reservas'),
     path('guardar_reserva/', views.guardar_reserva, name='guardar_reserva'),
     
     #Rutas para CRUD de reservas
    path('reservas/', views.ReservaListView.as_view(), name='listar_reservas'),
    path('reservas/nueva/', views.ReservaCreateView.as_view(), name='crear_reserva'),
    path('reservas/editar/<int:pk>/', views.ReservaUpdateView.as_view(), name='editar_reserva'),
    path('reservas/eliminar/<int:pk>/', views.ReservaDeleteView.as_view(), name='eliminar_reserva'),
     #Rutas para CRUD de cancelaciones
     path('cancelaciones/', views.CancelacionListView.as_view(), name='listar_cancelaciones'),
     path('cancelaciones/nueva/', views.CancelacionCreateView.as_view(), name='crear_cancelacion'),
     path('cancelaciones/editar/<int:pk>/', views.CancelacionUpdateView.as_view(), name='editar_cancelacion'),
     path('cancelaciones/eliminar/<int:pk>/', views.CancelacionDeleteView.as_view(), name='eliminar_cancelacion'),
    
     
]
