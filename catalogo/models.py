from django.db import models


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
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    nivel_dificultad = models.CharField(max_length=50)
    equipo_requerimiento = models.TextField()
    recomendacion_salud = models.TextField()

    class Meta:
        verbose_name = 'Actividad'
        verbose_name_plural = 'Actividades'

    def __str__(self):
        return self.nombre

class Paquete(models.Model):
    imagen = models.ImageField(upload_to='paquetes/', null=True, blank=True)
    nombre = models.CharField(max_length=200)
    descripcion = models.TextField()
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    duracion_estimada = models.CharField(max_length=100)
    punto_encuentro = models.CharField(max_length=200)
    codigo_categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE)
    actividades = models.ManyToManyField(Actividades)

    def __str__(self):
        return self.nombre
