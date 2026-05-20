from django import forms 
from django.forms import ModelForm 
from .models import Reserva, Cancelacion

# FORMULARIO DE RESERVA
class ReservaForm(ModelForm):
    class Meta:
        model = Reserva
        fields = ['usuario', 'paquete', 'fecha', 'numero_adultos', 'numero_menores', 'estado']
        widgets = {
            'usuario': forms.Select(attrs={'class': 'form-select'}),
            'paquete': forms.Select(attrs={'class': 'form-select'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'numero_adultos': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'numero_menores': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'estado': forms.Select(attrs={'class': 'form-select'}), 
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

        

