# En cada app: urls/__init__.py  ← vacío

# urls/public.py o urls/cliente.py o urls/admin.py
from django.urls import path
from reservas import views   # o: from nombre_app import views

app_name = 'reservas'   # ← cambia por cada app

urlpatterns = [
    # Se irán añadiendo las rutas
]