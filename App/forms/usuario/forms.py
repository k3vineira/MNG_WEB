import re
from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.contrib.auth.password_validation import validate_password
from App.models import Usuario


class PerfilTuristaForm(forms.ModelForm):
    """
    Formulario seguro para la actualización de perfil de usuario.
    Aplica una Lista Blanca estricta de campos editables. Cualquier campo
    crítico inyectado desde el navegador (como rol, is_staff, is_superuser, email, password)
    será automáticamente ignorado y descartado por Django.
    """
    imagen_perfil = forms.ImageField(
        required=False,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])],
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'id': 'id_imagen_perfil',
            'accept': 'image/png, image/jpeg, image/webp'
        }),
        error_messages={
            'invalid_image': 'El archivo subido no es una imagen válida (formatos permitidos: JPG, PNG, WebP).'
        }
    )

    class Meta:
        model = Usuario
        fields = [
            'first_name',
            'last_name',
            'telefono',
            'residencia',
            'imagen_perfil'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'first_name',
                'placeholder': 'Tu nombre'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'last_name',
                'placeholder': 'Tu apellido'
            }),
            'telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'telefono',
                'placeholder': '+57 300 123 4567'
            }),
            'residencia': forms.TextInput(attrs={
                'class': 'form-control',
                'id': 'residencia',
                'placeholder': 'Ciudad, País'
            }),
        }

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name', '').strip()
        if first_name and len(first_name) < 2:
            raise ValidationError("El nombre debe tener al menos 2 caracteres.")
        if first_name and not re.match(r'^[A-Za-záéíóúÁÉÍÓÚñÑ\s\.]+$', first_name):
            raise ValidationError("El nombre solo puede contener letras y espacios.")
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name', '').strip()
        if last_name and len(last_name) < 2:
            raise ValidationError("El apellido debe tener al menos 2 caracteres.")
        if last_name and not re.match(r'^[A-Za-záéíóúÁÉÍÓÚñÑ\s\.]+$', last_name):
            raise ValidationError("El apellido solo puede contener letras y espacios.")
        return last_name

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '').strip()
        if telefono:
            # Permitir dígitos, espacios, guiones y el prefijo '+'
            if not re.match(r'^\+?[0-9\s\-]{7,20}$', telefono):
                raise ValidationError("Ingresa un número telefónico válido (ej. +57 300 123 4567).")
        return telefono

    def clean_imagen_perfil(self):
        foto = self.cleaned_data.get('imagen_perfil')
        if foto and hasattr(foto, 'size'):
            max_mb = 4
            if foto.size > max_mb * 1024 * 1024:
                raise ValidationError(f"La foto de perfil no puede pesar más de {max_mb} MB.")
        return foto


class PerfilGuiaForm(PerfilTuristaForm):
    """Extensión segura para guías turísticos."""
    class Meta(PerfilTuristaForm.Meta):
        fields = PerfilTuristaForm.Meta.fields + [
            'numero_tarjeta_profesional',
            'entidad_salud'
        ]
        widgets = {
            **PerfilTuristaForm.Meta.widgets,
            'numero_tarjeta_profesional': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tarjeta profesional de guía'
            }),
            'entidad_salud': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'EPS / Entidad de salud'
            }),
        }


class CambiarClaveSeguraForm(forms.Form):
    """Formulario para cambio de contraseña con validación de política de seguridad."""
    current_password = forms.CharField(
        label="Contraseña Actual",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ingresa tu contraseña actual',
            'autocomplete': 'current-password'
        }),
        error_messages={'required': 'Debes ingresar tu contraseña actual.'}
    )
    new_password = forms.CharField(
        label="Nueva Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Mínimo 8 caracteres',
            'autocomplete': 'new-password'
        }),
        error_messages={'required': 'Debes ingresar la nueva contraseña.'}
    )
    confirm_password = forms.CharField(
        label="Confirmar Nueva Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Repite la nueva contraseña',
            'autocomplete': 'new-password'
        }),
        error_messages={'required': 'Debes confirmar la nueva contraseña.'}
    )

    def __init__(self, user=None, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if self.user and not self.user.check_password(current_password):
            raise ValidationError("La contraseña actual es incorrecta.")
        return current_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')

        if new_password and confirm_password:
            if new_password != confirm_password:
                self.add_error('confirm_password', "Las contraseñas nuevas no coinciden.")
            else:
                # Validar complejidad según configuraciones de Django (longitud, números, similitud)
                try:
                    validate_password(new_password, user=self.user)
                except ValidationError as error:
                    self.add_error('new_password', error)

        return cleaned_data
