from django import forms 
from django.forms import ModelForm 
from .models import Categoria, Actividades, Paquete, Tarifa , Temporada
import datetime


def generate_time_choices(start_hour=6, end_hour=18, step_minutes=15):
    choices = []
    current = datetime.datetime.combine(datetime.date.today(), datetime.time(start_hour, 0))
    end = datetime.datetime.combine(datetime.date.today(), datetime.time(end_hour, 0))
    while current <= end:
        value = current.strftime('%H:%M')
        display = current.strftime('%I:%M %p').lstrip('0').lower()
        choices.append((value, display))
        current += datetime.timedelta(minutes=step_minutes)
    return choices

TIME_CHOICES = generate_time_choices()

# FORMULARIO DE CATEGORÍA
class CategoriaForm(ModelForm):
    class Meta:
        model = Categoria 
        fields = '__all__' 
        widgets = {
            # Aplicas estilos CSS de Bootstrap para que se vea bien
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

# FORMULARIO DE ACTIVIDADES
class ActividadesForm(ModelForm):
    class Meta:
        model = Actividades
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'nivel_dificultad': forms.Select(attrs={'class': 'form-select'}), 
            'apto_para_menores': forms.CheckboxInput(attrs={'class': 'form-check-input'}), 
            'equipo_requerimiento': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'recomendacion_salud': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

# FORMULARIO DE PAQUETE
class PaqueteForm(ModelForm):
    hora_encuentro = forms.TimeField(
        widget=forms.Select(choices=TIME_CHOICES, attrs={'class': 'form-select'}),
        input_formats=['%H:%M'],
        required=True,
        label='Hora encuentro'
    )
    class Meta:
        model = Paquete
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'imagen': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control'}),
            'duracion_estimada': forms.TextInput(attrs={'class': 'form-control'}),
            'punto_encuentro': forms.TextInput(attrs={'class': 'form-control'}),
            # 'hora_encuentro' ahora se maneja como campo TimeField con Select arriba
            'categoria': forms.Select(attrs={'class': 'form-select'}),
            'actividades': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
class TarifaForm(ModelForm):
    class Meta:
        model = Tarifa
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
class TemporadaForm(ModelForm):
    class Meta:
        model = Temporada
        fields = ['nombre', 'fecha_inicio', 'fecha_fin', 'estado']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_inicio': forms.DateInput(
                format='%Y-%m-%d', 
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'fecha_fin': forms.DateInput(
                format='%Y-%m-%d', 
                attrs={'class': 'form-control', 'type': 'date'}
            ),
            'estado': forms.Select(choices=Temporada.ESTADOS,attrs={'class': 'form-select'} 
            ),
        }