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
            'first_name', 'last_name', 'telefono', 'residencia', 'imagen_perfil'
        ]

    def __init__(self, *args, **kwargs):
        """
        __init__.
        
        :param args: Descripción del parámetro.
        
        :param kwargs: Descripción del parámetro.
        
        :return: Respuesta de la función.
        """
        super().__init__(*args, **kwargs)
        self.fields['residencia'].required = False
