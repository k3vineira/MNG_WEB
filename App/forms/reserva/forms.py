from datetime import date, timedelta
from django import forms
from django.core.exceptions import ValidationError
from App.models import Reserva

class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['usuario', 'paquete', 'fecha_inicio', 'numero_adultos', 'numero_menores']
        widgets = {
            'usuario': forms.Select(attrs={'class': 'form-select'}),
            'paquete': forms.Select(attrs={'class': 'form-select'}),
            'fecha_inicio': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'numero_adultos': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'numero_menores': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Se exigen al menos 5 días de anticipación para reservas nuevas
        if not self.instance.pk:
            fecha_minima = date.today() + timedelta(days=5)
            self.fields['fecha'].widget.attrs['min'] = fecha_minima.strftime('%Y-%m-%d')

    def clean_fecha(self):
        fecha_reserva = self.cleaned_data.get('fecha')

        if self.instance.pk and self.instance.fecha == fecha_reserva:
            return fecha_reserva

        fecha_minima = date.today() + timedelta(days=5)

        if fecha_reserva:
            if fecha_reserva < date.today():
                raise ValidationError("No puedes seleccionar una fecha pasada.")
            
            if fecha_reserva < fecha_minima:
                raise ValidationError(
                    f"La reserva debe realizarse con al menos 5 días de anticipación "
                    f"(a partir del {fecha_minima.strftime('%d/%m/%Y')})."
                )

        return fecha_reserva

    def clean_numero_adultos(self):
        adultos = self.cleaned_data.get('numero_adultos')
        if adultos is None or adultos < 1:
            raise ValidationError("Debe haber al menos 1 adulto en la reserva.")
        return adultos

    def clean_numero_menores(self):
        menores = self.cleaned_data.get('numero_menores')
        if menores is None or menores < 0:
            raise ValidationError("El número de menores no puede ser negativo.")
        return menores

    def clean(self):
        cleaned_data = super().clean()
        adultos = cleaned_data.get('numero_adultos') or 0
        menores = cleaned_data.get('numero_menores') or 0

        if adultos + menores <= 0:
            raise ValidationError("La reserva debe incluir al menos una persona.")

        return cleaned_data