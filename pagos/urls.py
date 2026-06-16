from django.urls import path
from . import views

urlpatterns = [
    # Rutas para el usuario
    path('comprobantes/', views.enviar_comprobante, name='enviar_comprobante'),
    path('mis-comprobantes/', views.mis_comprobantes, name='mis_comprobantes'),

    # Rutas para el administrador
    path('admin/comprobantes/', views.admin_comprobantes,
         name='admin_comprobantes'),
    path('admin/comprobantes/revisar/<int:pk>/',
         views.admin_revisar_comprobante, name='admin_revisar_comprobante'),
    path('admin/comprobantes/eliminar/<int:pk>/',
         views.admin_eliminar_comprobante, name='admin_eliminar_comprobante'),

    path('mis-rechazos/', views.mis_rechazos, name='mis_rechazos'),
]
