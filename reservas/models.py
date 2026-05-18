from django.db import models
from django.conf import settings
from catalogo.models import Paquete

class Reserva(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada', 'Cancelada'),
    ]
    
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='reservas_realizadas', 
        verbose_name='Cliente'
    )
    paquete = models.ForeignKey(
        Paquete, 
        on_delete=models.PROTECT, 
        related_name='reserva', 
        verbose_name='Paquete Reservado'
    )
    fecha = models.DateField(verbose_name='Fecha de Reserva')
    numero_personas = models.PositiveIntegerField(verbose_name='Número de Personas')
    monto_total = models.IntegerField(verbose_name='Monto Total', editable=False)
    estado = models.CharField(
        max_length=20, 
        choices=ESTADO_CHOICES, 
        default='pendiente', 
        verbose_name='Estado'
    )

    class Meta:
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'

    def save(self, *args, **kwargs):
        if self.paquete and self.numero_personas:
            self.monto_total = self.paquete.precio * self.numero_personas
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Reserva {self.id} - {self.usuario.get_full_name()} ({self.paquete.nombre})"


class Cancelacion(models.Model):
    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE)
    motivo = models.TextField()
    penalidad = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'Cancelación'
        verbose_name_plural = 'Cancelaciones'

    def __str__(self):
        return f"Cancelación de Reserva {self.reserva.id}"