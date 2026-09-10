from django import forms
from django.core.exceptions import ValidationError
from django.forms import ModelForm
import re
from App.models import Promocion, Paquete


class PromocionForm(ModelForm):
    """Formulario para crear y editar promociones conforme a models.py y asociar paquetes turísticos."""

    paquetes = forms.ModelMultipleChoiceField(
        queryset=Paquete.objects.filter(estado=True),
        required=False,
        label="Paquetes a los que aplica",
        help_text="Selecciona uno o varios paquetes turísticos para vincular a esta promoción.",
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Promocion
        fields = [
            'nombre',
            'codigo_promocion',
            'porcentaje_descuento',
            'fecha_inicio',
            'fecha_fin',
            'codigo_cupon',
            'descripcion',
            'condiciones',
            'activa',
        ]
        labels = {
            'nombre': 'Nombre de la Promoción',
            'codigo_promocion': 'Código de Promoción',
            'porcentaje_descuento': 'Porcentaje de Descuento (%)',
            'fecha_inicio': 'Fecha de Inicio',
            'fecha_fin': 'Fecha de Finalización',
            'codigo_cupon': 'Código de Cupón (Opcional)',
            'descripcion': 'Descripción de la Oferta',
            'condiciones': 'Términos y Condiciones (Opcional)',
            'activa': '¿Promoción Activa?',
        }
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. Descuento Semana Santa 2026'}),
            'codigo_promocion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. PROM-SEMANASANTA-26'}),
            'porcentaje_descuento': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 100, 'placeholder': 'Ej. 20'}),
            'fecha_inicio': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'fecha_fin': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'codigo_cupon': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ej. MONAGUA20'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe los beneficios de esta promoción...'}),
            'condiciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Aplica sólo para fines de semana, no acumulable con otras ofertas...'}),
            'activa': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            # Inicializar los paquetes asociados actuales
            paquetes_ids = self.instance.paquetepromocion_set.values_list('paquete_id', flat=True)
            self.fields['paquetes'].initial = list(paquetes_ids)

    def clean_nombre(self):
        nombre = str(self.cleaned_data.get('nombre', '')).strip()
        if not re.search(r'[a-zA-ZáéíóúÁÉÍÓÚñÑ]', nombre):
            raise ValidationError("El nombre de la promoción debe contener letras.")
        return nombre

    def clean_codigo_promocion(self):
        codigo = str(self.cleaned_data.get('codigo_promocion', '')).strip().upper()
        if not codigo:
            raise ValidationError("El código de la promoción es obligatorio.")
        
        # Validar unicidad excluyendo la instancia actual
        qs = Promocion.objects.filter(codigo_promocion=codigo)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise ValidationError("Ya existe una promoción con este código de promoción.")
        return codigo

    def clean_codigo_cupon(self):
        cupon = self.cleaned_data.get('codigo_cupon')
        if cupon:
            cupon = str(cupon).strip().upper()
            qs = Promocion.objects.filter(codigo_cupon=cupon)
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise ValidationError("Ya existe una promoción con este código de cupón.")
            return cupon
        return None

    def clean_porcentaje_descuento(self):
        descuento = self.cleaned_data.get('porcentaje_descuento')
        if descuento is None or descuento < 1 or descuento > 100:
            raise ValidationError("El porcentaje de descuento debe encontrarse entre 1 y 100.")
        return descuento

    def clean(self):
        cleaned_data = super().clean()
        fecha_inicio = cleaned_data.get('fecha_inicio')
        fecha_fin = cleaned_data.get('fecha_fin')

        if fecha_inicio and fecha_fin:
            if fecha_fin < fecha_inicio:
                self.add_error('fecha_fin', "La fecha de fin no puede ser anterior a la fecha de inicio.")

        return cleaned_data
