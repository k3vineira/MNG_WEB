from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm
import re
from usuarios.models import Usuario


class CustomSetPasswordForm(SetPasswordForm):
    """
    Formulario personalizado para establecer una nueva contraseña.
    Valida que la nueva contraseña no sea idéntica a la actual.
    """
    def clean(self):
        """
        clean.
        
        :return: Respuesta de la función.
        """
        cleaned_data = super().clean()
        password = cleaned_data.get('new_password1')

        if password and self.user.check_password(password):
            raise forms.ValidationError(
                "La nueva contraseña no puede ser igual a la anterior. Por favor, elige una diferente."
            )
        return cleaned_data


class RecuperacionPersonalizadaForm(PasswordResetForm):
    """
    Formulario personalizado para la recuperación de contraseña.
    Exige apodo, número de documento y correo para mayor seguridad.
    """
    username = forms.CharField(
        label="Apodo", 
        max_length=150, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu apodo'})
    )
    numero_documento = forms.CharField(
        label="Número de Documento", 
        max_length=20, 
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu número de documento'})
    )

    def clean(self):
        """
        clean.
        
        :return: Respuesta de la función.
        """
        cleaned_data = super().clean()
        email = cleaned_data.get("email")
        username = cleaned_data.get("username")
        numero_documento = cleaned_data.get("numero_documento")

        if email and username and numero_documento:
            email_lower = email.lower()
            # Verificamos si existe el usuario con esos datos
            if not Usuario.objects.filter(
                email__iexact=email_lower,
                username__iexact=username,
                numero_documento=numero_documento
            ).exists():
                raise forms.ValidationError(
                    "Los datos proporcionados no coinciden con ninguna cuenta registrada en Monagua."
                )
        return cleaned_data


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
        """
        clean_numero_documento.
        
        :return: Respuesta de la función.
        """
        numero_documento = self.cleaned_data.get('numero_documento')
        if numero_documento:
            if Usuario.objects.filter(numero_documento=numero_documento).exists():
                raise forms.ValidationError(
                    "Ya existe un usuario registrado con este número de documento.")
        return numero_documento

    def clean_email(self):
        """
        clean_email.
        
        :return: Respuesta de la función.
        """
        email = self.cleaned_data.get('email')
        if email:
            email_lower = email.lower()
            if Usuario.objects.filter(email__iexact=email_lower).exists():
                raise forms.ValidationError(
                    "Ya existe un usuario registrado con este correo electrónico.")
        return email

    def clean_telefono(self):
        """
        clean_telefono.
        
        :return: Respuesta de la función.
        """
        telefono = self.cleaned_data.get('telefono')
        if telefono:
            if Usuario.objects.filter(telefono=telefono).exists():
                raise forms.ValidationError(
                    "Ya existe un usuario registrado con este número de teléfono.")
        return telefono

    def clean_first_name(self):
        """
        clean_first_name.
        
        :return: Respuesta de la función.
        """
        first_name = self.cleaned_data.get('first_name')
        if first_name:
            if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', first_name):
                raise forms.ValidationError(
                    "El nombre solo puede contener letras y espacios.")
        return first_name

    def clean_last_name(self):
        """
        clean_last_name.
        
        :return: Respuesta de la función.
        """
        last_name = self.cleaned_data.get('last_name')
        if last_name:
            if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', last_name):
                raise forms.ValidationError(
                    "Los apellidos solo pueden contener letras y espacios.")
        return last_name

    def clean_username(self):
        """
        clean_username.
        
        :return: Respuesta de la función.
        """
        username = self.cleaned_data.get('username')
        if username:
            if Usuario.objects.filter(username__iexact=username).exists():
                raise forms.ValidationError(
                    "Este nombre de usuario ya está en uso. Por favor, elige otro.")
        return username
