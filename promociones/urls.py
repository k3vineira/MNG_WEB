from django.urls import path
from promociones import views

urlpatterns = [
    
    path('gestion-promociones/', views.gestion_promociones, name='gestion_promociones'),
]