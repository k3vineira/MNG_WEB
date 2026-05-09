
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
    path('terminos/', views.terminos_view, name='terminos'),
    path('perfil/', views.perfil_view, name='detalles'),
]
