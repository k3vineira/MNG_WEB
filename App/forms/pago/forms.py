from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from App.models import Pago


class ComprobantePagoForm(forms.ModelForm):
    """
    Formulario seguro para la carga de comprobantes de pago por parte del turista.
    Aplica el principio de Lista Blanca para evitar 'Mass Assignment' y parameter tampering:
    Los campos 'monto', 'reserva' y 'estado_transaccion' están deliberadamente EXCLUIDOS
    del formulario y son fijados obligatoriamente por el servidor en la vista.
    """
    BANCOS_CHOICES = [
        ('', '— Selecciona el banco o medio de pago —'),
        ('Nequi', 'Nequi'),
        ('Daviplata', 'Daviplata'),
        ('Bancolombia', 'Bancolombia'),
        ('Banco de Bogotá', 'Banco de Bogotá'),
        ('Davivienda', 'Davivienda'),
        ('BBVA', 'BBVA'),
        ('Banco de Occidente', 'Banco de Occidente'),
        ('Lulo Bank', 'Lulo Bank'),
        ('RappiPay', 'RappiPay'),
        ('Otro', 'Otro (Especificar en descripción)'),
    ]

    METODOS_CHOICES = [
        ('Transferencia Bancaria', 'Transferencia Bancaria'),
        ('Billetera Digital', 'Billetera Digital (Nequi / Daviplata / etc.)'),
        ('Depósito en Corresponsal', 'Depósito en Corresponsal'),
        ('PSE / Enlace de Pago', 'PSE / Enlace de Pago'),
        ('Otro', 'Otro Método'),
    ]

    banco_origen = forms.ChoiceField(
        choices=BANCOS_CHOICES,
        required=True,
        widget=forms.Select(attrs={
            'class': 'select form-select',
            'id': 'id_banco_origen',
            'required': True
        }),
        error_messages={'required': 'Por favor selecciona un banco o medio de pago.'}
    )

    metodo_pago = forms.ChoiceField(
        choices=METODOS_CHOICES,
        required=False,
        initial='Transferencia Bancaria',
        widget=forms.Select(attrs={
            'class': 'select form-select',
            'id': 'id_metodo_pago'
        })
    )

    imagen_comprobante = forms.ImageField(
        required=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp', 'gif', 'pdf'])],
        widget=forms.ClearableFileInput(attrs={
            'class': 'clearablefileinput form-control',
            'id': 'id_imagen_comprobante',
            'accept': 'image/png, image/jpeg, image/webp, image/gif, application/pdf',
            'required': True
        }),
        error_messages={
            'required': 'Debes adjuntar la imagen o PDF del comprobante de pago.',
            'invalid_image': 'El archivo subido no es una imagen o archivo válido.'
        }
    )

    class Meta:
        model = Pago
        fields = [
            'referencia',
            'banco_origen',
            'metodo_pago',
            'imagen_comprobante',
            'descripcion'
        ]
        widgets = {
            'referencia': forms.TextInput(attrs={
                'class': 'textinput form-control',
                'id': 'id_referencia',
                'placeholder': 'Ej. CUS-123456789 o Nº Aprobación',
                'maxlength': '100',
                'required': True
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'textarea form-control',
                'id': 'id_descripcion',
                'rows': 3,
                'placeholder': 'Detalles adicionales o especificación de banco si seleccionaste Otro'
            }),
        }
        error_messages = {
            'referencia': {
                'required': 'El número de referencia o transacción es obligatorio.',
                'max_length': 'La referencia no puede exceder 100 caracteres.'
            }
        }

    def clean_referencia(self):
        referencia = self.cleaned_data.get('referencia', '').strip()
        if not referencia:
            raise ValidationError("La referencia de pago no puede estar vacía.")
        if len(referencia) < 3:
            raise ValidationError("La referencia debe contener al menos 3 caracteres.")
        return referencia

    def clean_imagen_comprobante(self):
        archivo = self.cleaned_data.get('imagen_comprobante')
        if archivo:
            # Límite de tamaño: 5 MB
            max_mb = 5
            if archivo.size > max_mb * 1024 * 1024:
                raise ValidationError(f"El comprobante no puede pesar más de {max_mb} MB.")
        return archivo
