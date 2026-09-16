from django import forms
from App.models import PQRS
from App.models import Seguimiento, Reserva

class PqrsForm(forms.ModelForm):
    reserva = forms.ModelChoiceField(
        queryset=Reserva.objects.none(),
        required=False,
        label="Reserva Afectada (Opcional)",
        empty_label="-- Selecciona la reserva vinculada --"
    )

    class Meta:
        model = PQRS
        fields = ['tipo', 'asunto', 'descripcion', 'nombre_completo', 'correo']
        labels = {
            'tipo': 'Tipo de Solicitud',
            'asunto': 'Asunto de la PQRS',
            'descripcion': 'Detalle de su solicitud',
            'nombre_completo': 'Nombre Completo',
            'correo': 'Correo Electrónico',
        }
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Cuéntanos más...'}),
            'nombre_completo': forms.TextInput(attrs={'placeholder': 'Ej. Juan Pérez'}),
            'correo': forms.EmailInput(attrs={'placeholder': 'tu@email.com'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and user.is_authenticated:
            # Si el usuario está logueado, filtramos sus reservas
            self.fields['reserva'].queryset = Reserva.objects.filter(usuario=user)
            # Y ocultamos los campos de visitante anónimo ya que tomaremos sus datos
            self.fields['nombre_completo'].widget = forms.HiddenInput()
            self.fields['nombre_completo'].required = False
            self.fields['correo'].widget = forms.HiddenInput()
            self.fields['correo'].required = False
        else:
            # Si no hay usuario, ocultamos el campo reserva y hacemos obligatorios nombre y correo
            self.fields['reserva'].widget = forms.HiddenInput()
            self.fields['reserva'].required = False
            self.fields['nombre_completo'].required = True
            self.fields['correo'].required = True

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