from django import forms 
from django.forms import ModelForm 
from .models import Categoria, Actividades, Paquete # 

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
            'nivel_dificultad': forms.Select(attrs={'class': 'form-select'}), # Menú desplegable
            'equipo_requerimiento': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'recomendacion_salud': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
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
            'codigo_categoria': forms.Select(attrs={'class': 'form-select'}),
            
            'actividades': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }