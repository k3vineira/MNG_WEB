from django import forms
from .models import PQRS, Blog

class PqrsForm(forms.ModelForm):
    class Meta:
        model = PQRS
       
        fields = ['cliente', 'tipo', 'asunto', 'descripcion']
        
        
        labels = {
            'cliente': 'Nombre Completo',
            'tipo': 'Tipo de Solicitud',
            'asunto': 'Asunto de la PQRS',
            'descripcion': 'Detalle de su solicitud',
        }
        
       
        widgets = {
            'descripcion': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Cuéntanos más...'}),
        }
class BlogForm(forms.ModelForm):
    class Meta:
        model = Blog
        fields = ['titulo', 'contenido','imagen', 'publicado']
        labels = {
            'titulo': 'Título del Blog',
            'contenido': 'Contenido del Blog',
            'imagen': 'Imagen del Blog',
            'fecha_publicacion': 'Fecha de Publicación',
            'publicado': '¿Publicar ahora?'
        }     
        widgets = {
            'contenido': forms.Textarea(attrs={'rows': 10, 'placeholder': 'Escribe el contenido del blog aquí...'}),
            'publicado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        