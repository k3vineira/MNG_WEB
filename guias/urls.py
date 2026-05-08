# En cada app: urls/__init__.py  ← vacío

# urls/public.py o urls/cliente.py o urls/admin.py
from django.urls import path
from guias import views   # o: from nombre_app import views

app_name = 'guias'   # ← cambia por cada app

urlpatterns = [
    # Se irán añadiendo las rutas
]