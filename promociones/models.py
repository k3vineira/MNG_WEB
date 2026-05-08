from django.db import models
from catalogo.models import Paquete

class Promocion(models.Model):
    nombre_promocion = models.CharField(max_length=150)
    descripcion      = models.TextField(blank=True)
    descuento        = models.DecimalField(max_digits=5, decimal_places=2)  # porcentaje
    fecha_inicio     = models.DateField()
    fecha_fin        = models.DateField()
    imagen           = models.ImageField(upload_to='promociones/', blank=True, null=True)
    activa           = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.nombre_promocion} ({self.descuento}%)"

class PaquetePromocion(models.Model):
    paquete   = models.ForeignKey(Paquete, on_delete=models.CASCADE)
    promocion = models.ForeignKey(Promocion, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('paquete', 'promocion')