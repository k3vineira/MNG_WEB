from django.urls import path
from catalogo import views

app_name = 'public'

urlpatterns = [
    path('', views.inicio, name='inicio'),       

]