import os
from django.db import models
from django.conf import settings


class ComprobantePago(models.Model):
    ESTADO_CHOICES = [
        ('pendiente',  'Pendiente de revisión'),
        ('aprobado',   'Aprobado'),
        ('rechazado',  'Rechazado'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comprobantes',
        verbose_name='Usuario'
    )

    # Vincular con una reserva específica
    reserva = models.ForeignKey(
        'reservas.Reserva',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='comprobantes',
        verbose_name='Reserva'
    )

    referencia = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Número de referencia / transacción',
        help_text='Número de comprobante, transacción o referencia bancaria'
    )
    banco_origen = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Banco / medio de pago'
    )
    monto = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Monto pagado'
    )
    imagen = models.ImageField(
        upload_to='comprobantes/%Y/%m/',
        verbose_name='Imagen del comprobante'
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name='Descripción / nota adicional'
    )
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        default='pendiente',
        verbose_name='Estado'
    )
    nota_admin = models.TextField(
        blank=True,
        verbose_name='Nota del administrador'
    )
    fecha_envio = models.DateTimeField(
        auto_now_add=True, verbose_name='Fecha de envío')
    fecha_revision = models.DateTimeField(
        null=True, blank=True, verbose_name='Fecha de revisión')

    class Meta:
        verbose_name = 'Comprobante de Pago'
        verbose_name_plural = 'Comprobantes de Pago'
        ordering = ['-fecha_envio']

    def __str__(self):
        """
        __str__.
        
        :return: Respuesta de la función.
        """
        return f"Comprobante #{self.pk} — {self.usuario.username} — {self.get_estado_display()}"

    def nombre_archivo(self):
        """
        nombre_archivo.
        
        :return: Respuesta de la función.
        """
        return os.path.basename(self.imagen.name) if self.imagen else '—'
