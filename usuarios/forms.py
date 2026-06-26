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

    def clean_numero_documento(self):
        numero_documento = self.cleaned_data.get('numero_documento')
        if numero_documento:
            if Usuario.objects.filter(numero_documento=numero_documento).exists():
                raise forms.ValidationError(
                    "Ya existe un usuario registrado con este número de documento.")
        return numero_documento

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            email_lower = email.lower()
            if Usuario.objects.filter(email__iexact=email_lower).exists():
                raise forms.ValidationError(
                    "Ya existe un usuario registrado con este correo electrónico.")
        return email


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
