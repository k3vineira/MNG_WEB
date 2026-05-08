from django.db import models
from usuarios.models import GuiaTuristico
from catalogo.models import Paquete

class PlanGuia(models.Model):
    ESTADO_CHOICES = [
        ('programado', 'Programado'),
        ('en_curso',   'En Curso'),
        ('finalizado', 'Finalizado'),
    ]
    guia         = models.ForeignKey(GuiaTuristico, on_delete=models.PROTECT, related_name='planes')
    paquete      = models.ForeignKey(Paquete, on_delete=models.PROTECT)
    fecha_inicio = models.DateField()
    fecha_fin    = models.DateField()
    estado       = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='programado')
    notas        = models.TextField(blank=True)

    def __str__(self):
        return f"{self.guia} → {self.paquete} ({self.fecha_inicio})"