from django.urls import path
from App.views import views
from App.views.paquete import views as paquete_views
from App.views.reserva import views as reserva_views
from App.views.pago import views as pago_views
from App.views.terminos_y_condiciones import views as terminos_views
from App.views.notificacion import views as notificacion_views
from App.views.bitacora import views as bitacora_views
from App.views.accesibilidad import views as accesibilidad_views

urlpatterns = [
    # Accesibilidad API
    path('api/accesibilidad/save/', accesibilidad_views.guardar_accesibilidad, name='guardar_accesibilidad'),

    # Inicio
    path('', views.index, name='index'),

    # Términos y Condiciones & Nosotros
    path('terminos-y-condiciones/', terminos_views.terminos_view, name='terminos'),
    path('nosotros/', terminos_views.nosotros_view, name='nosotros'),

    # Tours / Paquetes públicos
    path('tours/', paquete_views.tours, name='tours'),

    # Tours / Paquetes (Administración / Staff)
    path('admin/paquetes/', paquete_views.PaqueteListView.as_view(), name='listar_paquetes'),
    path('admin/paquetes/agregar/', paquete_views.PaqueteCreateView.as_view(), name='agregar_paquete'),
    path('admin/paquetes/editar/<int:pk>/', paquete_views.PaqueteUpdateView.as_view(), name='editar_paquete'),
    path('admin/paquetes/eliminar/<int:pk>/', paquete_views.PaqueteDeleteView.as_view(), name='eliminar_paquete'),

    # Reservas (Usuario / Turista)
    path('reservas/reservar/', reserva_views.reservas_view, name='reservas'),
    path('reservas/guardar/<int:paquete_id>/', reserva_views.guardar_reserva, name='guardar_reserva'),
    path('reservas/mis-reservas/', reserva_views.mis_reservas_usuario, name='mis_reservas_usuario'),
    path('reservas/carrito/', reserva_views.carrito_view, name='carrito'),
    path('reservas/cancelar/<int:reserva_id>/', reserva_views.cancelar_reserva_usuario, name='cancelar_reserva_usuario'),
    path('reservas/comprobante/<int:reserva_id>/', reserva_views.comprobante_reserva_html, name='comprobante_reserva'),
    path('reservas/comprobante-multiple/', reserva_views.comprobante_multiple, name='comprobante_multiple'),

    # Blog
    # path('blog/', views.blog_list, name='blog'),
    
    # Pagos (Usuario / Turista)
    path('pagos/enviar-comprobante/', pago_views.enviar_comprobante, name='enviar_comprobante'),
    path('pagos/mis-comprobantes/', pago_views.mis_comprobantes, name='mis_comprobantes'),

    # Notificaciones
    path('notificaciones/', notificacion_views.listar_notificaciones, name='listar_notificaciones'),
    path('notificaciones/marcar-leida/<int:notificacion_id>/', notificacion_views.marcar_notificacion_leida, name='marcar_notificacion_leida'),
    path('notificaciones/eliminar/<int:notificacion_id>/', notificacion_views.eliminar_notificacion, name='eliminar_notificacion'),

    # Bitácora
    path('bitacora/', bitacora_views.listar_bitacora, name='listar_bitacora'),
    path('bitacora/<int:bitacora_id>/', bitacora_views.detalle_bitacora, name='detalle_bitacora'),

    # Reservas (Administración / Staff)
    path('admin/reservas/', reserva_views.ReservaListView.as_view(), name='listar_reservas'),
    path('admin/reservas/agregar/', reserva_views.ReservaCreateView.as_view(), name='agregar_reserva'),
    path('admin/reservas/editar/<int:pk>/', reserva_views.ReservaUpdateView.as_view(), name='editar_reserva'),
    path('admin/reservas/eliminar/<int:pk>/', reserva_views.ReservaDeleteView.as_view(), name='eliminar_reserva'),
    path('admin/reservas/cambiar-estado/<int:reserva_id>/', reserva_views.cambiar_estado_reserva, name='cambiar_estado_reserva'),
]