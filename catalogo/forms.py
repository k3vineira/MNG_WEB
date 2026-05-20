from django import forms 
from django.forms import ModelForm 
from .models import Categoria, Actividades, Paquete, Tarifa , Temporada

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
    class Meta:
        model = Paquete
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control'}),
            'precio': forms.NumberInput(attrs={'class': 'form-control'}),
            'duracion_estimada': forms.TextInput(attrs={'class': 'form-control'}),
            'punto_encuentro': forms.TextInput(attrs={'class': 'form-control'}),
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
        fields = '__all__'
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_inicio': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
