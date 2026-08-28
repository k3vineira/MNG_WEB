from App.models import Categoria
from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm
import re


class CategoriaForm(ModelForm):
    """Formulario para crear y editar categorías de paquetes turísticos."""

    class Meta:
        model = Categoria
        exclude = ['estado']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'pattern': r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$',
                'title': 'El nombre de la categoría solo debe contener letras, no números.'
            }),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_nombre(self):
        nombre = str(self.cleaned_data.get('nombre', '')).strip()

        if not nombre:
            raise ValidationError("El nombre de la categoría es obligatorio.")

        
        if not re.search(r'[a-zA-ZáéíóúÁÉÍÓÚñÑ]', nombre):
            raise ValidationError("El nombre de la categoría debe contener letras.")


        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]+$', nombre):
            raise ValidationError("El nombre de la categoría solo debe contener letras y espacios, no se permiten números.")

        return nombre

    def clean_descripcion(self):
        descripcion = str(self.cleaned_data.get('descripcion', '')).strip()

        if not descripcion:
            raise ValidationError("La descripción es obligatoria.")

    
        if descripcion.isdigit():
            raise ValidationError("La descripción no puede contener únicamente números.")

        if not re.search(r'[a-zA-ZáéíóúÁÉÍÓÚñÑ]', descripcion):
            raise ValidationError("La descripción debe incluir un texto explicativo con letras.")

        return descripcion