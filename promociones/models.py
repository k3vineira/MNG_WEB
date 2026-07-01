from django.db import models
from catalogo.models import Paquete

class Promocion(models.Model):
    paquete = models.ForeignKey(Paquete, on_delete=models.CASCADE, related_name='promociones')
    nombre = models.CharField(max_length=150, verbose_name="Nombre de la promoción")
    descripcion = models.TextField(verbose_name="Descripción")
    descuento = models.PositiveIntegerField(verbose_name="Porcentaje de descuento")
    fecha_fin = models.DateField(verbose_name="Fecha de fin")
    activa = models.BooleanField(default=True, verbose_name="¿Activa?")

    class Meta:
        verbose_name = "Promoción"
        verbose_name_plural = "Promociones"

    def __str__(self):
        return f"{self.nombre} ({self.descuento}%)"

class Banner(models.Model):
    imagen = models.ImageField(upload_to='banners/', verbose_name="Imagen del Banner")
    titulo = models.CharField(max_length=150, verbose_name="Título del Banner")
    enlace = models.URLField(blank=True, null=True, verbose_name="Enlace (Opcional)")
    activo = models.BooleanField(default=True, verbose_name="¿Activo?")

    class Meta:
        verbose_name = "Banner"
        verbose_name_plural = "Banners"

    def __str__(self):
        return self.titulo
