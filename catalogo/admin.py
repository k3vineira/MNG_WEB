from django.contrib import admin
from .models import Categoria, Actividades, Paquete, PaqueteActividad

admin.site.register(Categoria)
admin.site.register(Actividades)
admin.site.register(Paquete)
admin.site.register(PaqueteActividad)
