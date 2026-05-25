from django import forms 
from django.forms import ModelForm, Select, DateInput, NumberInput
from .models import Reserva, Cancelacion


# FORMULARIO DE RESERVA
class ReservaForm(ModelForm):
    class Meta:
        model = Reserva
        fields = ['usuario', 'paquete', 'fecha', 'numero_adultos', 'numero_menores', 'estado']
        widgets = {
            'usuario': Select(attrs={'class': 'form-select'}),
            'paquete': Select(attrs={'class': 'form-select'}),
            'fecha': DateInput(
                format='%Y-%m-%d', 
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'numero_adultos': NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'numero_menores': NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'estado': Select(attrs={'class': 'form-select'}), 
        }

class CancelacionForm(ModelForm):
    class Meta:
        model = Cancelacion
        fields = ['reserva', 'motivo', 'penalidad', 'estado'] 
        widgets = {
            # Bloqueo visual para que el usuario no lo mueva, pero el navegador sí envíe el dato
            'reserva': forms.Select(attrs={
                'class': 'form-control bg-light', 
                'style': 'pointer-events: none;',
                'readonly': 'readonly'
            }),
            'motivo': forms.Textarea(attrs={'class': 'form-control bg-light', 'rows': 3, 'readonly': 'readonly'}),
            'penalidad': forms.NumberInput(attrs={'class': 'form-control'}),
            'estado': forms.Select(attrs={'class': 'form-select'}), 
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Aquí NO va ninguna línea que use .disabled = True
        if self.instance and self.instance.penalidad:
            self.initial['penalidad'] = int(self.instance.penalidad)