from App.models import Blog
from django import forms


class BlogForm(forms.ModelForm):
    class Meta:
        model = Blog
        fields = ['titulo', 'contenido',
                  'informacion_adicional', 'imagen_destacada', 'estado']
        labels = {
            'titulo': 'Título del Blog',
            'contenido': 'Contenido del Blog',
            'informacion_adicional': 'Información Adicional',
            'imagen_destacada': 'Imagen del Blog',
            'fecha_publicacion': 'Fecha de Publicación',
            'estado': '¿Publicar ahora?',
        }
        widgets = {
            'contenido': forms.Textarea(attrs={'rows': 6, 'placeholder': 'Escribe el contenido del blog aquí...'}),
            'informacion_adicional': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Agrega información adicional si es necesario...'}),
            'estado': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            
        }