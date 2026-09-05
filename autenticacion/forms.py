from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth import authenticate
from App.models import Usuario
import re


class IniciarSesionForm(forms.Form):
    """Formulario de inicio de sesión por usuario o correo y contraseña."""
    usuario_o_email = forms.CharField(
        label="Usuario o Correo Electrónico",
        widget=forms.TextInput(attrs={
            'class': 'form-control rounded-pill py-3 px-4',
            'placeholder': 'Correo electrónico o nombre de usuario',
            'required': True,
            'autocomplete': 'username'
        })
    )
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control rounded-pill py-3 px-4 pe-5',
            'placeholder': 'Contraseña',
            'required': True,
            'autocomplete': 'current-password'
        })
    )


class RegistroForm(forms.ModelForm):
    """Formulario de registro completo de nuevos clientes en Monagua."""
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control rounded-pill py-3 px-4',
            'placeholder': 'Mínimo 8 caracteres',
            'required': True
        })
    )
    confirmar_password = forms.CharField(
        label="Confirmar Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control rounded-pill py-3 px-4',
            'placeholder': 'Repite tu contraseña',
            'required': True
        })
    )

    class Meta:
        model = Usuario
        fields = [
            'first_name', 'last_name', 'username', 'email',
            'tipo_documento', 'numero_documento', 'telefono', 'residencia',
            'pais', 'departamento', 'ciudad'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control rounded-pill py-3 px-4', 'placeholder': 'Nombre'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control rounded-pill py-3 px-4', 'placeholder': 'Apellido'}),
            'username': forms.TextInput(attrs={'class': 'form-control rounded-pill py-3 px-4', 'placeholder': 'aventurero_mongua'}),
            'email': forms.EmailInput(attrs={'class': 'form-control rounded-pill py-3 px-4', 'placeholder': 'correo@ejemplo.com'}),
            'tipo_documento': forms.Select(attrs={'class': 'form-select rounded-pill py-3 px-4'}),
            'numero_documento': forms.TextInput(attrs={'class': 'form-control rounded-pill py-3 px-4', 'placeholder': 'Número de documento'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control rounded-pill py-3 px-4', 'placeholder': '+57 300 000 0000'}),
            'residencia': forms.TextInput(attrs={'class': 'form-control rounded-pill py-3 px-4', 'placeholder': 'Ciudad, País'}),
            'pais': forms.TextInput(attrs={'class': 'form-control'}),
            'departamento': forms.NumberInput(attrs={'class': 'form-control'}),
            'ciudad': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def clean_username(self):
        username = self.cleaned_data.get('username', '').strip()
        if Usuario.objects.filter(username__iexact=username).exists():
            raise ValidationError("Este nombre de usuario ya está registrado.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if Usuario.objects.filter(email__iexact=email).exists():
            raise ValidationError("Ya existe una cuenta vinculada a este correo electrónico.")
        return email

    def clean_numero_documento(self):
        doc = self.cleaned_data.get('numero_documento', '').strip()
        if Usuario.objects.filter(numero_documento=doc).exists():
            raise ValidationError("Este número de documento ya está registrado.")
        return doc

    def clean_telefono(self):
        tel = self.cleaned_data.get('telefono', '').strip()
        if tel and Usuario.objects.filter(telefono=tel).exists():
            raise ValidationError("Este número de teléfono ya está registrado.")
        return tel

    def clean_departamento(self):
        dep = self.cleaned_data.get('departamento')
        return dep if dep else None

    def clean_ciudad(self):
        ciu = self.cleaned_data.get('ciudad')
        return ciu if ciu else None

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        confirmar_password = cleaned_data.get("confirmar_password")

        if password and confirmar_password:
            if password != confirmar_password:
                self.add_error('confirmar_password', "Las contraseñas no coinciden.")
            if len(password) < 6:
                self.add_error('password', "La contraseña debe tener al menos 6 caracteres.")

        return cleaned_data


class RecuperacionPersonalizadaForm(forms.Form):
    """Formulario para solicitar restablecimiento validando username, documento y email."""
    username = forms.CharField(
        label="Apodo (Nombre de usuario)",
        widget=forms.TextInput(attrs={
            'class': 'form-control rounded-pill py-3 px-4',
            'placeholder': 'aventurero_mongua',
            'required': True
        })
    )
    numero_documento = forms.CharField(
        label="Número de Documento",
        widget=forms.TextInput(attrs={
            'class': 'form-control rounded-pill py-3 px-4',
            'placeholder': '1000000000',
            'required': True
        })
    )
    email = forms.EmailField(
        label="Correo Electrónico",
        widget=forms.EmailInput(attrs={
            'class': 'form-control rounded-pill py-3 px-4',
            'placeholder': 'aventura@monagua.com',
            'required': True
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username', '').strip()
        numero_documento = cleaned_data.get('numero_documento', '').strip()
        email = cleaned_data.get('email', '').strip().lower()

        if username and numero_documento and email:
            usuario = Usuario.objects.filter(
                username__iexact=username,
                numero_documento=numero_documento,
                email__iexact=email
            ).first()

            if not usuario:
                raise ValidationError(
                    "Los datos ingresados no coinciden con ninguna cuenta activa en Monagua. "
                    "Verifica tu apodo, documento y correo."
                )
            cleaned_data['usuario_encontrado'] = usuario

        return cleaned_data


class RestablecerClaveForm(forms.Form):
    """Formulario para ingresar y confirmar la nueva contraseña tras validar token."""
    new_password1 = forms.CharField(
        label="Nueva Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control rounded-pill py-3 px-4 pe-5',
            'placeholder': '••••••••',
            'required': True,
            'minlength': '6'
        })
    )
    new_password2 = forms.CharField(
        label="Confirmar Nueva Contraseña",
        widget=forms.PasswordInput(attrs={
            'class': 'form-control rounded-pill py-3 px-4 pe-5',
            'placeholder': '••••••••',
            'required': True,
            'minlength': '6'
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('new_password1')
        p2 = cleaned_data.get('new_password2')

        if p1 and p2:
            if p1 != p2:
                self.add_error('new_password2', "Las contraseñas no coinciden.")
            if len(p1) < 6:
                self.add_error('new_password1', "La contraseña debe tener al menos 6 caracteres.")

        return cleaned_data


# Alias para retrocompatibilidad
LoginForm = IniciarSesionForm
RecuperarPasswordForm = RecuperacionPersonalizadaForm
