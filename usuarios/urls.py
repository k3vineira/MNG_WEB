from django.urls import path
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('inicio/', views.inicio_usuarios, name='inicio'),
    path('dashboard/', views.dashboard_admin, name='dashboard'),
    
    # Autenticación
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
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
    path('perfil/', views.perfil_view, name='detalles'),
    
    # Gestión
    path('guias/', views.gestion_guias, name='gestion_guias'),
    path('guias/rol/<int:user_id>/', views.asignar_rol_guia, name='asignar_rol_guia'),
    path('guias/estado/<int:id>/<str:estado>/', views.guias_baja_reactivar, name='guias_baja_reactivar'),
    path('guias/guardar/', views.guias_guardar, name='guias_guardar'),
    path('terminos/', views.terminos_view, name='terminos'),

    # Flujo de Restablecimiento de Contraseña
    path('password-reset/', views.PasswordResetViewCustom.as_view(), name='password_reset'),
    path('password-reset/done/', views.PasswordResetDoneViewCustom.as_view(), name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', views.PasswordResetConfirmViewCustom.as_view(), name='password_reset_confirm'),
    path('password-reset-complete/', views.PasswordResetCompleteViewCustom.as_view(), name='password_reset_complete'),
]