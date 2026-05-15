from django.db import models
from django.conf import settings
from catalogo.models import Paquete

class Reserva(models.Model):
    # Relación con el usuario (Cliente)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='reservas_realizadas', 
        verbose_name='Cliente'
    )
    
    paquete = models.ForeignKey(Paquete, on_delete=models.PROTECT, related_name='reserva', verbose_name='Paquete Reservado')
    fecha = models.DateField(verbose_name='Fecha de Reserva')
    numero_adultos = models.PositiveIntegerField(verbose_name='Número de Adultos', default=1)
    numero_menores = models.PositiveIntegerField(verbose_name='Número de Menores', default=0)
    
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
    ]
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='pendiente', verbose_name='Estado')
    
    # Monto total (se calculará automáticamente)
    monto_total = models.IntegerField(verbose_name='Monto Total', editable=False)
    
    fecha_registro = models.DateTimeField(auto_now_add=True, verbose_name='Fecha de Registro')

    class Meta:
        verbose_name = 'Reserva'
        verbose_name_plural = 'Reservas'

    def save(self, *args, **kwargs):
        if self.paquete and self.fecha:
            try:
                from catalogo.models import Temporada, Tarifa
                temporada = Temporada.objects.get(fecha_inicio__lte=self.fecha, fecha_fin__gte=self.fecha)
                tarifa = Tarifa.objects.get(paquete=self.paquete, temporada=temporada)
                self.monto_total = (tarifa.precio_adulto * self.numero_adultos) + (tarifa.precio_menor * self.numero_menores)
            except (Temporada.DoesNotExist, Tarifa.DoesNotExist):
                self.monto_total = 0
        elif not getattr(self, 'monto_total', None):
            self.monto_total = 0
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Reserva {self.id} - {self.usuario.get_full_name()} ({self.paquete.nombre})"
    

class Cancelacion(models.Model):
    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE)
    motivo = models.TextField()
    penalidad = models.DecimalField(max_digits=10, decimal_places=2, default=0)
