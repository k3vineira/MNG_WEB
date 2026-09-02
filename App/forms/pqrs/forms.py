from django import forms
from App.models import PQRS
from App.models import Seguimiento, Reserva

class PqrsForm(forms.ModelForm):
    class Meta:
        model = PQRS

        fields = ['tipo', 'asunto', 'descripcion']
        labels = {
            'tipo': 'Tipo de Solicitud',
            'asunto': 'Asunto de la PQRS',
            'descripcion': 'Detalle de su solicitud',
        }

        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Cuéntanos más...'}),
        }



class SeguimientoForm(forms.ModelForm):
    reserva = forms.ModelChoiceField(
        queryset=Reserva.objects.none(),
        required=False,
        empty_label="-- Seleccione una reserva relacionada (Opcional) --",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Reserva Asociada'
    )

    class Meta:
        model = Seguimiento
        fields = ['reserva', 'respuesta']
        labels = {
            'respuesta': 'Detalle / Mensaje de Seguimiento',
        }
        widgets = {
            'respuesta': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Escribe la respuesta o nota de seguimiento...'}),
        }

    def __init__(self, *args, **kwargs):
        # Filtramos las reservas correspondientes al usuario recibido
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user and user.is_authenticated:
            self.fields['reserva'].queryset = Reserva.objects.filter(usuario=user)