from django.db import models
from usuarios.models import Cliente
from catalogo.models import Paquete, Horario

class Reserva(models.Model):
    ESTADO_CHOICES = [
        ('pendiente',  'Pendiente'),
        ('confirmada', 'Confirmada'),
        ('cancelada',  'Cancelada'),
        ('completada', 'Completada'),
    ]
    cliente      = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='reservas')
    paquete      = models.ForeignKey(Paquete, on_delete=models.PROTECT)
    horario      = models.ForeignKey(Horario, on_delete=models.PROTECT, null=True, blank=True)
    num_personas = models.PositiveIntegerField(default=1)
    estado       = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='pendiente')
    fecha_reserva= models.DateTimeField(auto_now_add=True)
    observaciones= models.TextField(blank=True)

    def __str__(self):
        return f"Reserva #{self.pk} — {self.cliente} | {self.paquete}"

class Cancelacion(models.Model):
    reserva = models.OneToOneField(Reserva, on_delete=models.CASCADE)
    motivo  = models.TextField()
    fecha   = models.DateTimeField(auto_now_add=True)
    penalidad = models.DecimalField(max_digits=10, decimal_places=2, default=0)

class SeguroViaje(models.Model):
    reserva     = models.OneToOneField(Reserva, on_delete=models.CASCADE)
    proveedor   = models.CharField(max_length=100)
    numero_poliza = models.CharField(max_length=80)
    cobertura   = models.TextField(blank=True)
    costo       = models.DecimalField(max_digits=10, decimal_places=2)