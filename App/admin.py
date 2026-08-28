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


class SeguimientoAdmin(admin.ModelAdmin):
    list_display = ('id', 'pqrs', 'usuario', 'reserva', 'fecha_respuesta')
    list_filter = ('fecha_respuesta',)
    search_fields = ('pqrs__asunto', 'usuario__username', 'respuesta')
    ordering = ('-fecha_respuesta',)


class BitacoraAdmin(admin.ModelAdmin):
    list_display = ('fecha_registro', 'usuario', 'accion', 'modulo', 'registro_id', 'seguimiento', 'reserva', 'pago', 'pqrs', 'ip_origen')
    list_filter = ('accion', 'modulo', 'fecha_registro')
    search_fields = ('modulo', 'registro_id', 'usuario__username', 'ip_origen', 'descripcion')
    readonly_fields = (
        'fecha_registro', 'usuario', 'seguimiento', 'reserva', 'pqrs', 'pago',
        'accion', 'modulo', 'registro_id', 'ip_origen', 'descripcion'
    )
    ordering = ('-fecha_registro',)

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
admin.site.register(Seguimiento, SeguimientoAdmin)
admin.site.register(Reserva)

admin.site.register(Calificacion)
admin.site.register(PlanGuia)
admin.site.register(Pago)
admin.site.register(Promocion)
admin.site.register(PolizaViaje)
admin.site.register(Aseguradora)
admin.site.register(Bitacora, BitacoraAdmin)


