from datetime import date, timedelta
from django import forms
from django.core.exceptions import ValidationError
from App.models import Reserva

class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['usuario', 'paquete', 'fecha_inicio', 'numero_adultos', 'numero_menores', 'estado_reserva']
        labels = {
            'usuario': 'Cliente / Titular',
            'paquete': 'Paquete / Tour',
            'fecha_inicio': 'Fecha del Viaje',
            'numero_adultos': 'Número de Adultos',
            'numero_menores': 'Número de Menores',
            'estado_reserva': 'Estado de la Reserva',
        }
        widgets = {
            'usuario': forms.Select(attrs={'class': 'form-select'}),
            'paquete': forms.Select(attrs={'class': 'form-select'}),
            'fecha_inicio': forms.DateInput(
                format='%Y-%m-%d',
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'numero_adultos': forms.NumberInput(attrs={'class': 'form-control', 'min': '1'}),
            'numero_menores': forms.NumberInput(attrs={'class': 'form-control', 'min': '0'}),
            'estado_reserva': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Se exigen al menos 5 días de anticipación para reservas nuevas
        if not self.instance.pk:
            fecha_minima = date.today() + timedelta(days=5)
            if 'fecha_inicio' in self.fields:
                self.fields['fecha_inicio'].widget.attrs['min'] = fecha_minima.strftime('%Y-%m-%d')
    def clean_fecha_inicio(self):
        fecha_reserva = self.cleaned_data.get('fecha_inicio')

        if not fecha_reserva:
            return fecha_reserva

        # Si estás editando una reserva ya guardada y no cambias la fecha, la permite sin exigir los 5 días
        if self.instance.pk and self.instance.fecha_inicio == fecha_reserva:
            return fecha_reserva

        hoy = date.today()
        fecha_minima = hoy + timedelta(days=5)

        # 1. Validar que no sea fecha pasada
        if fecha_reserva < hoy:
            raise ValidationError("No puedes seleccionar una fecha pasada.")

        # 2. Validar mínimo 5 días de anticipación
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