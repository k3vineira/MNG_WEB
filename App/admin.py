from django.contrib import admin
from .models import Usuario, Temporada, Categoria, Actividades, Paquete, Tarifa, PaqueteActividad, Blog, PQRS, Seguimiento, Reserva, Auditoria, Calificacion, PlanGuia, Pago, Promocion, PolizaViaje, Aseguradora

# Registros simples de modelos de la aplicación en el panel de administración
admin.site.register(Usuario)
admin.site.register(Temporada)
admin.site.register(Categoria)
admin.site.register(Actividades)
admin.site.register(Paquete)
admin.site.register(Tarifa)
admin.site.register(PaqueteActividad)
admin.site.register(Blog)
admin.site.register(PQRS)
admin.site.register(Seguimiento)
admin.site.register(Reserva)
admin.site.register(Auditoria)
admin.site.register(Calificacion)
admin.site.register(PlanGuia)
admin.site.register(Pago)
admin.site.register(Promocion)
admin.site.register(PolizaViaje)
admin.site.register(Aseguradora)
