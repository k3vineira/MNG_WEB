from django.urls import path
from App.views import views

urlpatterns = [
    path('', views.index, name='index'),
    path('Tours/', views.tours, name='tours'),
]