from django.urls import path
from . import views  

urlpatterns = [
    path('marcar-leida/<int:noti_id>/', views.marcar_notificacion_leida, name='marcar_leida'),
    path('historial/', views.lista_notificaciones, name='lista_notificaciones'),
]