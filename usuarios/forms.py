from django import forms
from .models import Usuario



class PerfilUsuarioForm(forms.ModelForm):
    """
    Formulario especializado para la actualización de perfil de usuario.
    Incluye validación automática de campos únicos y limpieza de datos.
    """
    class Meta:
        model = Usuario
        fields = [
            'first_name', 'last_name', 'tipo_documento',
            'numero_documento', 'telefono', 'residencia', 'imagen_perfil'
        ]
