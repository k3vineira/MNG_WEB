from django.urls import path
from . import views
from .views import login_view, logout_view


app_name = 'usuarios'

urlpatterns = [
    path('', views.inicio_usuarios, name='inicio'),
    path('dashboard/', views.dashboard_admin, name='dashboard'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('registro/', views.registro_view, name='registro'),
    
    # Rutas públicas (Nosotros y Términos)
    path('terminos/', views.terminos_view, name='terminos'),
    path('nosotros/', views.nosotros_view, name='nosotros'), # <-- Nueva ruta
    
    path('perfil/', views.perfil_view, name='detalles'),
    
    # Rutas de Gestión de Personal y Guías
    path('gestion-guias/', views.gestion_guias, name='gestion_guias'),
    path('gestion-guias/<int:id>/', views.gestion_guias, name='gestion_guias_sel'),
    path('asignar-rol-guia/<int:user_id>/', views.asignar_rol_guia, name='asignar_rol_guia'),
    path('guia-estado/<int:id>/<str:estado>/', views.guias_baja_reactivar, name='guias_baja_reactivar'),
    path('guias-guardar/', views.guias_guardar, name='guias_guardar'),
]