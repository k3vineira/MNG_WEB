from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario

class RegistroForm(UserCreationForm):
    """
    Formulario personalizado para registrar usuarios en Monagua.
    Hereda de UserCreationForm para manejar el hashing de contraseñas automáticamente.
    """
    class Meta:
        model = Usuario
        fields = (
            'username', 'email', 'first_name', 'last_name', 
            'tipo_documento', 'numero_documento', 'telefono'
        )

class PerfilUsuarioForm(forms.ModelForm):
    """
    Formulario especializado para la actualización de perfil de usuario.
    Incluye validación automática de campos únicos y limpieza de datos.
    """
    class Meta:
        model = Usuario
        fields = [
            'first_name', 'last_name', 'tipo_documento', 
            'numero_documento', 'telefono', 'residencia'
        ]