from django.db import models
from usuarios.models import Cliente
from catalogo.models import Paquete

class Pago(models.Model):
    ESTADOS_PAGO = [
        ('pendiente', 'Pendiente'),
        ('completado', 'Completado'),
        ('fallido', 'Fallido'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='pagos')
    tour = models.ForeignKey(Paquete, on_delete=models.CASCADE)
    fecha_reserva = models.DateTimeField(auto_now_add=True)
    total_pagado = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=20, choices=ESTADOS_PAGO, default='pendiente')
    metodo_pago = models.CharField(max_length=50, blank=True)
    referencia_pago = models.CharField(max_length=100, unique=True, null=True)

    def __str__(self):
        return f"Pago #MON-{self.id} - {self.cliente}"
