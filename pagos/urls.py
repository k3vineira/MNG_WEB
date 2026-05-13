from django.urls import path
from . import views

app_name = 'pagos' # Define el namespace para la aplicación 'pagos'

urlpatterns = [
    path('mis-pagos/', views.mis_pagos, name='mis_pagos'),
    path('descargar-recibo/<int:pago_id>/', views.descargar_recibo, name='descargar_recibo'),
    path('mis-pagos/', views.mis_pagos, name='mis_pagos'),
]