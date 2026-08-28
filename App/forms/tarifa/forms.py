    
from App.models import Tarifa
from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm
import re
class TarifaForm(ModelForm):
    
    """Formulario para crear y editar tarifas asociadas a un paquete y temporada."""

    class Meta:
        model = Tarifa
        exclude = ['estado']
        widgets = {
            'paquete': forms.Select(attrs={'class': 'form-select'}),
            'temporada': forms.Select(attrs={'class': 'form-select'}),
            'precio_adulto': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'precio_menor': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }

    def clean_precio_adulto(self):
        precio = self.cleaned_data.get('precio_adulto')
        if precio is not None and precio <= 0:
            raise ValidationError("El precio para adulto debe ser mayor a 0.")
        return precio

    def clean_precio_menor(self):
        precio = self.cleaned_data.get('precio_menor')
        if precio is not None and precio < 0:
            raise ValidationError("El precio para menor no puede ser un valor negativo.")
        return precio
