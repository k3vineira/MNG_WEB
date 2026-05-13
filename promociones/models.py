from django.db import models

class Promocion(models.Model):
    nombre = models.CharField(max_length=100, verbose_name="Título del Banner")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    imagen = models.ImageField(upload_to='promociones/', blank=True, null=True)
    enlace = models.URLField(blank=True, null=True, verbose_name="URL de destino")
    fecha_inicio = models.DateField(blank=True, null=True)
    fecha_fin = models.DateField(blank=True, null=True)
    porcentaje_descuento = models.PositiveIntegerField(default=0)
    activo = models.BooleanField(default=True)
    prioridad = models.IntegerField(default=0, help_text="Orden de aparición")
    solo_usuarios = models.BooleanField(default=False, verbose_name="Solo para registrados")
    creado_en = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Promoción"
        verbose_name_plural = "Promociones"
        ordering = ['prioridad', '-creado_en']

    def __str__(self):
        return self.nombre
