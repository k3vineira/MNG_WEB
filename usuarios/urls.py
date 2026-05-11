
from django.urls import path
from . import views
from .views import login_view


app_name = 'usuarios'

urlpatterns = [
    path('', views.inicio_usuarios, name='inicio'),
    path('login/', login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('terminos/', views.terminos_view, name='terminos'),
]
