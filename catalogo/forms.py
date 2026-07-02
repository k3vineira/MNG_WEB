"""
Formularios de gestión para el catálogo: categorías, actividades, paquetes, tarifas y temporadas.
"""

from django import forms
from django.forms import ModelForm
from .models import Categoria, Actividades, Paquete, Tarifa, Temporada


class CategoriaForm(ModelForm):
    """Formulario para crear y editar categorías de paquetes turísticos."""
    class Meta:
        model = Categoria
        exclude = ['estado']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class ActividadesForm(ModelForm):
    """Formulario para crear y editar actividades turísticas."""
    class Meta:
        model = Actividades
        exclude = ['estado']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'nivel_dificultad': forms.Select(attrs={'class': 'form-select'}),
            'apto_para_menores': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'equipo_requerimiento': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'recomendacion_salud': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class PaqueteForm(ModelForm):
    """Formulario para crear y editar paquetes turísticos incluyendo imagen y actividades."""
    class Meta:
        model = Paquete
        exclude = ['estado']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control'}),
            'duracion_estimada': forms.TextInput(attrs={'class': 'form-control'}),
            'punto_encuentro': forms.TextInput(attrs={'class': 'form-control'}),
            'hora_encuentro': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'actividades': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }


class TarifaForm(ModelForm):
    """Formulario para crear y editar tarifas asociadas a un paquete y temporada."""
    class Meta:
        model = Tarifa
        exclude = ['estado']
        widgets = {
            'paquete': forms.Select(attrs={'class': 'form-select'}),
            'temporada': forms.Select(attrs={'class': 'form-select'}),
            'precio_adulto': forms.NumberInput(attrs={'class': 'form-control'}),
            'precio_menor': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class TemporadaForm(ModelForm):
    """Formulario para crear y editar temporadas turísticas con fechas de vigencia."""
    class Meta:
        model = Temporada
        fields = ['nombre', 'fecha_inicio', 'fecha_fin']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_inicio': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'fecha_fin': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'form-control', 'type': 'date'}
            ),
        }
