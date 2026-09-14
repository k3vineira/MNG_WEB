from App.models import Tarifa, Paquete, Temporada
from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm


class TarifaForm(ModelForm):
    """Formulario para crear y editar tarifas asociadas a un paquete y temporada."""

    class Meta:
        model = Tarifa
        fields = ['paquete', 'temporada', 'precio_adulto', 'precio_menor', 'estado']
        widgets = {
            'paquete': forms.Select(attrs={'class': 'form-select'}),
            'temporada': forms.Select(attrs={'class': 'form-select'}),
            'precio_adulto': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': 'Ej. 50000'}),
            'precio_menor': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'placeholder': 'Ej. 35000'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['paquete'].queryset = Paquete.objects.all()
        self.fields['temporada'].queryset = Temporada.objects.all()

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

    def clean(self):
        cleaned_data = super().clean()
        paquete = cleaned_data.get('paquete')
        temporada = cleaned_data.get('temporada')

        if paquete and temporada:
            qs = Tarifa.objects.filter(paquete=paquete, temporada=temporada)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("Ya existe una tarifa configurada para este paquete en la temporada seleccionada.")

        return cleaned_data

