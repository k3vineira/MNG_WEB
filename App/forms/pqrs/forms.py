from App.models import PQRS
from django import forms
from django.forms import ModelForm


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
    