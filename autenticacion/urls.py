from django.urls import path
from . import views

urlpatterns = [
    # Inicio y Cierre de Sesión (Predeterminados)
    path('login/', views.login_vista, name='login'),
    path('logout/', views.logout_vista, name='logout'),

    # Registro de Usuarios y Validación OTP
    path('registro/', views.registro_vista, name='registro'),
    path('registro/verificar-otp/', views.verificar_otp_registro_vista, name='verificar_otp_registro'),

    # Recuperación de Nombre de Usuario / Apodo
    path('recuperar-apodo/', views.recuperar_apodo_vista, name='recuperar_apodo'),

    # Recuperación de Contraseña con OTP y Enlace
    path('recuperar-clave/', views.recuperar_clave_vista, name='recuperar_clave'),
    path('recuperar-clave/verificar-otp/', views.verificar_otp_recuperar_vista, name='verificar_otp_clave'),
    path('recuperar-clave/enviado/', views.restablecer_clave_enviado_vista, name='clave_enviada'),
    path('recuperar-clave/confirmar/<uidb64>/<token>/', views.restablecer_clave_confirmar_vista, name='confirmar_clave'),
    path('recuperar-clave/guardada/', views.restablecer_clave_guardar_vista, name='clave_guardada'),

    # Verificación en Tiempo Real (AJAX)
    path('ajax/verificar-campo/', views.verificar_campo_ajax, name='verificar_campo_ajax'),
    path('verificar-campo/', views.verificar_campo_ajax, name='verificar_campo_directo'),

    # APIs Geográficas Locales (dr5hn)
    path('api/paises/', views.api_paises, name='api_paises'),
    path('api/departamentos/<str:pais_id>/', views.api_departamentos, name='api_departamentos'),
    path('api/ciudades/<int:departamento_id>/', views.api_ciudades, name='api_ciudades'),
]
