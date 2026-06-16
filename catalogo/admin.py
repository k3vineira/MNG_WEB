from django.contrib import admin
from .models import Temporada, Categoria, Actividades, Paquete, Tarifa, PaqueteActividad

# Register your models here.
admin.site.register(Temporada)
admin.site.register(Categoria)
admin.site.register(Actividades)
admin.site.register(Paquete)
admin.site.register(Tarifa)
admin.site.register(PaqueteActividad)
