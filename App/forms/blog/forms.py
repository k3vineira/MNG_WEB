from django import forms
from App.models import Blog


class BlogForm(forms.ModelForm):
    class Meta:
        model = Blog
        fields = ['titulo', 'contenido', 'informacion_adicional', 'imagen_destacada', 'estado']
        labels = {
            'titulo': 'Título de la publicación',
            'contenido': 'Contenido del blog',
            'informacion_adicional': 'Información adicional / consejos',
            'imagen_destacada': 'Imagen destacada / portada',
            'estado': '¿Publicar en el sitio ahora?',
        }
        widgets = {
            'titulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej. Los mejores senderos y atractivos naturales de Mongua'
            }),
            'contenido': forms.Textarea(attrs={
                'rows': 6,
                'class': 'form-control',
                'placeholder': 'Escribe aquí el contenido del artículo o noticia...'
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if 'estado' in self.fields:
            self.fields['estado'].label = '¿Publicar en el sitio ahora?'
            self.fields['estado'].help_text = ''

        if 'imagen_destacada' in self.fields:
            self.fields['imagen_destacada'].label = 'Imagen destacada / portada'
            self.fields['imagen_destacada'].widget.attrs['accept'] = 'image/*'
            self.fields['imagen_destacada'].widget.attrs['title'] = 'Seleccionar imagen'
        }

    def clean_titulo(self):
        titulo = str(self.cleaned_data.get('titulo', '')).strip()
        if not titulo:
            raise forms.ValidationError("El título del artículo es obligatorio.")
        if len(titulo) < 5:
            raise forms.ValidationError("El título debe contener al menos 5 caracteres.")
        if titulo.isdigit():
            raise forms.ValidationError("El título no puede contener únicamente números.")
        return titulo

    def clean_contenido(self):
        contenido = str(self.cleaned_data.get('contenido', '')).strip()
        if not contenido:
            raise forms.ValidationError("El contenido del artículo es obligatorio.")
        if len(contenido) < 20:
            raise forms.ValidationError("El contenido debe tener al menos 20 caracteres para aportar información valiosa.")
        return contenido
