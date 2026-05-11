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