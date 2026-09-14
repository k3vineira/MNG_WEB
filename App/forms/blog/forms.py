from django import forms
from App.models import Blog


class BlogForm(forms.ModelForm):
    class Meta:
        model = Blog
        fields = ['titulo', 'contenido', 'informacion_adicional', 'imagen_destacada', 'estado']
        labels = {
            'titulo': 'Título de la Publicación',
            'contenido': 'Contenido del Blog',
            'informacion_adicional': 'Información Adicional / Consejos',
            'imagen_destacada': 'Imagen Destacada / Portada',
            'estado': '¿Publicar inmediatamente en el sitio?',
        }
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. Los mejores senderos y atractivos naturales de Mongua'
            }),
            'contenido': forms.Textarea(attrs={
                'rows': 6,
                'class': 'form-control',
                'placeholder': 'Escribe aquí el cuerpo del artículo o noticia...'
            }),
            'informacion_adicional': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Agrega datos de interés, recomendaciones para viajeros o notas adicionales...'
            }),
            'imagen_destacada': forms.ClearableFileInput(attrs={
                'class': 'form-control'
            }),
            'estado': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }