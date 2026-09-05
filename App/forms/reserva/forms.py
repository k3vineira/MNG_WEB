from django import forms
from App.models import Reserva


class ReservaForm(forms.ModelForm):
    """Formulario para crear y editar reservas de paquetes turísticos."""

    class Meta:
        model = Reserva
        fields = ['paquete', 'usuario', 'fecha_inicio', 'numero_adultos', 'numero_menores', 'estado_reserva', 'motivo_cancelacion']
        widgets = {
            'paquete': forms.Select(attrs={'class': 'form-select'}),
            'usuario': forms.Select(attrs={'class': 'form-select'}),
            'fecha_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'numero_adultos': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'numero_menores': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'estado_reserva': forms.Select(attrs={'class': 'form-select'}),
            'motivo_cancelacion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def clean_numero_adultos(self):
        adultos = self.cleaned_data.get('numero_adultos')
        if adultos is None or adultos < 1:
            raise forms.ValidationError("Debe haber al menos 1 adulto en la reserva.")
        return adultos

    def clean_numero_menores(self):
        menores = self.cleaned_data.get('numero_menores')
        if menores is None or menores < 0:
            raise forms.ValidationError("El número de menores no puede ser un valor negativo.")
        return menores
