from django import forms
from django.forms import ModelForm, Select, DateInput, NumberInput
from .models import Reserva, Cancelacion



class ReservaForm(ModelForm):
    class Meta:
        model = Reserva
        fields = ['usuario', 'paquete', 'fecha',
                  'numero_adultos', 'numero_menores']
        widgets = {
            'usuario': Select(attrs={'class': 'form-select'}),
            'paquete': Select(attrs={'class': 'form-select'}),
            'fecha': DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'numero_adultos': NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'numero_menores': NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }


class CancelacionForm(forms.ModelForm):
    class Meta:
        model = Cancelacion
        fields = ['reserva', 'motivo']
        widgets = {
            'reserva': forms.Select(attrs={
                'class': 'form-control bg-light',
                'style': 'pointer-events: none;',
                'readonly': 'readonly'
            }),
            'motivo': forms.Textarea(attrs={
                'class': 'form-control bg-light', 
                'rows': 3, 
                'readonly': 'readonly'
            }),
        }