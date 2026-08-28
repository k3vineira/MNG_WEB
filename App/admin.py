from django.contrib import admin
from .models import Usuario, Temporada, Categoria, Actividades, Paquete, Tarifa, PaqueteActividad, Blog, PQRS, Seguimiento, Reserva, Calificacion, PlanGuia, Pago, Promocion, PolizaViaje, Aseguradora, Bitacora

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


class BitacoraAdmin(admin.ModelAdmin):
    list_display = ('fecha_accion', 'usuario', 'accion_realizada', 'tabla_afectada', 'registro_afectado_id', 'direccion_ip')
    list_filter = ('accion_realizada', 'tabla_afectada', 'fecha_accion')
    search_fields = ('tabla_afectada', 'registro_afectado_id', 'usuario__username', 'direccion_ip', 'observacion')
    readonly_fields = ('fecha_accion', 'usuario', 'accion_realizada', 'tabla_afectada', 'registro_afectado_id', 'direccion_ip', 'observacion', 'valor_anterior', 'nuevo_valor')
    ordering = ('-fecha_accion',)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

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

admin.site.register(Calificacion)
admin.site.register(PlanGuia)
admin.site.register(Pago)
admin.site.register(Promocion)
admin.site.register(PolizaViaje)
admin.site.register(Aseguradora)
admin.site.register(Bitacora, BitacoraAdmin)


