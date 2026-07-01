from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .forms import CustomSetPasswordForm


urlpatterns = [
    # Autenticación y Registro
    path('login/', views.UsuarioLoginView.as_view(), name='login'),
    path('logout/', views.UsuarioLogoutView.as_view(), name='logout'),
    path('registro/', views.registro_view, name='registro'),
    path('registro/otp/', views.registro_otp_verify_view, name='registro_otp'),
    path('verificar-disponibilidad/', views.verificar_disponibilidad, name='verificar_disponibilidad'),
    path('recuperar-apodo/', views.recuperar_apodo_view, name='recuperar_apodo'),

    # Recuperación de contraseña
    path('password-reset/', views.password_reset_request_view, name='password_reset'),
    path('password-reset/otp/', views.password_reset_otp_verify_view, name='password_reset_otp'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='authentication/contraseña_reset_enviado.html'), name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='authentication/contraseña_reset_form.html', form_class=CustomSetPasswordForm, success_url='/autenticacion/password-reset/complete/'), name='password_reset_confirm'),
    path('password-reset/complete/', auth_views.PasswordResetCompleteView.as_view(template_name='authentication/contraseña_reset_guardar.html'), name='password_reset_complete'),
]
