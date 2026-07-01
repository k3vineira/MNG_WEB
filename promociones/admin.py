from django.contrib import admin
from .models import Promocion, Banner

@admin.register(Promocion)
class PromocionAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'paquete', 'descuento', 'fecha_fin', 'activa')
    list_filter = ('activa', 'fecha_fin')
    search_fields = ('nombre', 'paquete__nombre')

@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'activo')
    list_filter = ('activo',)
    search_fields = ('titulo',)
