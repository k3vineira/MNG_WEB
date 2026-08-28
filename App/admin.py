from django.contrib import admin
from .models import Usuario, Temporada, Categoria, Actividades, Paquete, Tarifa, PaqueteActividad, Blog, PQRS, Seguimiento, Reserva, Auditoria, Calificacion, PlanGuia, Pago, Promocion, PolizaViaje, Aseguradora

class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'rol', 'get_pais', 'get_departamento', 'get_ciudad', 'is_active')

    def get_pais(self, obj):
        return obj.pais_nombre
    get_pais.short_description = 'País'

    def get_departamento(self, obj):
        return obj.departamento_nombre
    get_departamento.short_description = 'Departamento'

    def get_ciudad(self, obj):
        return obj.ciudad_nombre
    get_ciudad.short_description = 'Ciudad'

admin.site.register(Usuario, UsuarioAdmin)
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
