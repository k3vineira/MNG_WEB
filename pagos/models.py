from django.db import models
from reservas.models import Reserva

class Pago(models.Model):
    METODO_CHOICES = [
        ('efectivo',      'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('tarjeta',       'Tarjeta'),
        ('nequi',         'Nequi'),
    ]
    ESTADO_CHOICES = [
        ('pendiente',  'Pendiente'),
        ('verificado', 'Verificado'),
        ('rechazado',  'Rechazado'),
    ]
    reserva      = models.ForeignKey(Reserva, on_delete=models.PROTECT, related_name='pagos')
    monto        = models.DecimalField(max_digits=10, decimal_places=2)
    metodo_pago  = models.CharField(max_length=20, choices=METODO_CHOICES)
    estado       = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='pendiente')
    comprobante  = models.ImageField(upload_to='comprobantes_pagos/', blank=True, null=True)
    fecha_pago   = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Pago #{self.pk} — {self.reserva}"

class Factura(models.Model):
    reserva      = models.OneToOneField(Reserva, on_delete=models.PROTECT)
    pago         = models.ForeignKey(Pago, on_delete=models.PROTECT)
    numero       = models.CharField(max_length=20, unique=True)
    fecha_emision= models.DateTimeField(auto_now_add=True)
    subtotal     = models.DecimalField(max_digits=10, decimal_places=2)
    descuento    = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total        = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Factura {self.numero}"