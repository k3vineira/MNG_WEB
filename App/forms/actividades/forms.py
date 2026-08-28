from App.models import Actividades
from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm
import re

class ActividadesForm(ModelForm):
    """Formulario para crear y editar actividades turísticas."""

    class Meta:
        model = Actividades
        exclude = ['estado']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'nivel_dificultad': forms.Select(attrs={'class': 'form-select'}),
            'apto_menores': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'equipo_requerimiento': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'recomendaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean_nombre(self):
        nombre = str(self.cleaned_data.get('nombre', '')).strip()

        if not nombre:
            raise ValidationError("El nombre de la actividad es obligatorio.")

        if nombre.isdigit():
            raise ValidationError("El nombre de la actividad no puede ser solo números.")

        if not re.search(r'[a-zA-ZáéíóúÁÉÍÓÚñÑ]', nombre):
            raise ValidationError("El nombre de la actividad debe contener letras.")

        return nombre
