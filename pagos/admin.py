from django.contrib import admin
from .models import ComprobantePago

@admin.register(ComprobantePago)
class ComprobantePagoAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'reserva', 'referencia', 'banco_origen', 'monto', 'estado', 'fecha_envio')
    list_filter = ('estado', 'banco_origen', 'fecha_envio')
    search_fields = ('usuario__username', 'usuario__email', 'referencia', 'banco_origen')
    readonly_fields = ('fecha_envio',)
    ordering = ('-fecha_envio',)
