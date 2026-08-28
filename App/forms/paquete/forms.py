from App.models import Paquete
from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm
import re


class PaqueteForm(ModelForm):
    """Formulario para crear y editar paquetes turísticos incluyendo imagen y actividades."""

    class Meta:
        model = Paquete
        exclude = ['estado']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'imagen': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*',
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'pattern': '.*[a-zA-ZáéíóúÁÉÍÓÚñÑ].*',
                'title': 'La descripción debe contener texto y no solo números.'
            }),
            'precio': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'dias_duracion': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'noches_duracion': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'duracion_estimada': forms.TextInput(attrs={'class': 'form-control'}),
            'punto_encuentro': forms.TextInput(attrs={
                'class': 'form-control',
                'pattern': '.*[a-zA-ZáéíóúÁÉÍÓÚñÑ].*',
                'title': 'El punto de encuentro debe incluir letras o el nombre de un lugar, no solo números.'
            }),
            'hora_encuentro': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'actividades': forms.CheckboxSelectMultiple(attrs={
                'class': 'form-check-input'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if not self.instance.pk:
            self.fields['imagen'].required = True
            self.fields['imagen'].widget.attrs['required'] = 'required'

    def clean_nombre(self):
        nombre = str(self.cleaned_data.get('nombre', '')).strip()
        if not re.search(r'[a-zA-ZáéíóúÁÉÍÓÚñÑ]', nombre):
            raise ValidationError("El nombre del paquete debe contener texto y no solo números.")
        return nombre

    def clean_descripcion(self):
        descripcion = str(self.cleaned_data.get('descripcion', '')).strip()

        if not descripcion:
            raise ValidationError("La descripción es obligatoria.")

        if descripcion.isdigit():
            raise ValidationError("La descripción no puede contener solo números. Ingresa un texto descriptivo.")

        if not re.search(r'[a-zA-ZáéíóúÁÉÍÓÚñÑ]', descripcion):
            raise ValidationError("La descripción debe contener letras y detalles explicativos.")

        return descripcion

    def clean_precio(self):
        precio = self.cleaned_data.get('precio')
        if precio is not None and precio <= 0:
            raise ValidationError("El precio del paquete debe ser mayor a 0.")
        return precio

    def clean_punto_encuentro(self):
        punto = str(self.cleaned_data.get('punto_encuentro', '')).strip()

        if punto.isdigit():
            raise ValidationError("El punto de encuentro no puede contener solo números. Ingresa un lugar o dirección válida.")

        if not re.search(r'[a-zA-ZáéíóúÁÉÍÓÚñÑ]', punto):
            raise ValidationError("El punto de encuentro debe incluir el nombre de un lugar o texto válido.")

        return punto

    def clean_dias_duracion(self):
        dias = self.cleaned_data.get('dias_duracion')
        if dias is None or dias < 1:
            raise ValidationError("Los días de duración deben ser al menos 1.")
        return dias

    def clean_noches_duracion(self):
        noches = self.cleaned_data.get('noches_duracion')
        if noches is None or noches < 0:
            raise ValidationError("Las noches de duración no pueden ser un valor negativo.")
        return noches