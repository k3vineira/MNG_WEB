"""
Configuración del sitio de administración de Django para la gestión de usuarios.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Cliente, GuiaTuristico


class CustomUserAdmin(UserAdmin):
    """
    Administrador personalizado para el modelo Usuario.
    Extiende UserAdmin para mostrar campos adicionales como rol y documento.
    """
    fieldsets = UserAdmin.fieldsets + (
        ('Información de Perfil', {'fields': (
            'rol', 'tipo_documento', 'numero_documento', 'telefono', 'residencia', 'imagen_perfil')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Información de Perfil', {'fields': (
            'rol', 'tipo_documento', 'numero_documento', 'telefono', 'residencia', 'imagen_perfil')}),
    )
    list_display = ('username', 'email', 'first_name',
                    'last_name', 'rol', 'is_staff')
    list_filter = ('rol', 'is_staff', 'is_superuser', 'is_active')
    search_fields = ('username', 'email', 'first_name',
                     'last_name', 'numero_documento')


admin.site.register(Usuario, CustomUserAdmin)
admin.site.register(Cliente)
admin.site.register(GuiaTuristico)
