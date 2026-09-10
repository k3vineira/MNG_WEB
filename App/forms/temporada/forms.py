from App.models import Temporada
from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm
import re

class TemporadaForm(ModelForm):
    """Formulario para crear y editar temporadas turísticas con fechas de vigencia."""

    class Meta:
        model = Temporada
        fields = ['nombre', 'descripcion', 'fecha_inicio', 'fecha_fin', 'estado']
        labels = {
            'nombre': 'Nombre de la Temporada',
            'descripcion': 'Descripción',
            'fecha_inicio': 'Fecha de Inicio',
            'fecha_fin': 'Fecha de Finalización',
            'estado': '¿Está Activa?',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fecha_inicio': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'fecha_fin': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def clean_nombre(self):
        nombre = str(self.cleaned_data.get('nombre', '')).strip()
        if not re.search(r'[a-zA-ZáéíóúÁÉÍÓÚñÑ]', nombre):
            raise ValidationError("El nombre de la temporada debe contener letras (ej: 'Temporada Alta 2026').")
        return nombre

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')

        if fecha_inicio and fecha_fin:
            if fecha_fin < fecha_inicio:
                raise ValidationError("La fecha de fin no puede ser anterior a la fecha de inicio.")

        return cleaned_data
    