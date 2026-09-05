from django.urls import path
from App.views import views
from App.views.paquete import views as paquete_views

urlpatterns = [
    path('', views.index, name='index'),
    path('Tours/', paquete_views.tours, name='tours'),
]