from django.db import models
from django.conf import settings


class Categoria(models.Model):
    nombre = models.CharField(max_length=100, verbose_name='Nombre de la Categoría')
    descripcion = models.TextField(verbose_name='Descripción')
    estado = models.BooleanField(default=True, verbose_name='¿Está Activa?')

    class Meta:
        verbose_name = 'Categoría'
        verbose_name_plural = 'Categorías'

    def __str__(self):
        return self.nombre

class Actividades(models.Model):
    NIVEL_CHOICES = [
        ('Alta', 'Alta'),
        ('Media', 'Media'),
        ('Baja', 'Baja'),
    ]
    nombre = models.CharField(max_length=100, verbose_name='Nombre de la Actividad')
    descripcion = models.TextField(verbose_name='Descripción')
    nivel_dificultad = models.CharField(max_length=10, choices=NIVEL_CHOICES, verbose_name='Nivel de Dificultad')
    equipo_requerimiento = models.TextField(verbose_name='Equipo Requerido')
    recomendacion_salud = models.TextField(verbose_name='Recomendaciones de Salud')
    class Meta:
        verbose_name = 'Actividad'
        verbose_name_plural = 'Actividades'

    def __str__(self):
        return self.nombre

class Paquete(models.Model):
    imagen = models.ImageField(upload_to='destinos/', null=True, blank=True)
    nombre = models.CharField(max_length=100, verbose_name='Nombre del Paquete')
    descripcion = models.TextField(verbose_name='Descripción')
    precio = models.IntegerField(verbose_name='Precio Total')
    duracion_estimada = models.CharField(max_length=50)
    punto_encuentro = models.CharField(max_length=200)
    codigo_categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    actividades = models.ManyToManyField(Actividades, through='PaqueteActividad')


class PaqueteActividad(models.Model):
    codigo_paquete_act = models.AutoField(primary_key=True)

    codigo_paquete = models.ForeignKey(
        Paquete,
        on_delete=models.CASCADE
    )

    codigo_actividad = models.ForeignKey(
        Actividades,
        on_delete=models.CASCADE
    )
    class Meta:
        db_table = 'paquete_actividades'