from django import forms 
from django.forms import ModelForm 
from .models import Reserva, Cancelacion

# FORMULARIO DE RESERVA
class ReservaForm(ModelForm):
    class Meta:
        model = Reserva
        fields = '__all__'
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-control'}),
            'paquete': forms.Select(attrs={'class': 'form-control'}),
            'horario': forms.Select(attrs={'class': 'form-control'}),
            'num_personas': forms.NumberInput(attrs={'class': 'form-control'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'observaciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class CancelacionForm(ModelForm):
    class Meta:
        model = Cancelacion
        fields = '__all__'
        widgets = {
            'reserva': forms.Select(attrs={'class': 'form-control'}),
            'motivo': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'penalidad': forms.NumberInput(attrs={'class': 'form-control'}),
        }

        

