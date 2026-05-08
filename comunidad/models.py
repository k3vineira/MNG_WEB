from django.db import models

# Create your models here.
class Calificacion(models.Model):
    cliente   = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    paquete   = models.ForeignKey(Paquete, on_delete=models.CASCADE)
    puntaje   = models.PositiveSmallIntegerField()   
    comentario= models.TextField(blank=True)
    fecha     = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cliente', 'paquete')


class Blog(models.Model):
    titulo             = models.CharField(max_length=200)
    contenido          = models.TextField()
    resumen            = models.CharField(max_length=300, blank=True)
    imagen             = models.ImageField(upload_to='blog/', blank=True, null=True)
    categoria          = models.CharField(max_length=80, blank=True)
    fecha_publicacion  = models.DateTimeField(auto_now_add=True)
    publicado          = models.BooleanField(default=True)

    class Meta:
        ordering = ['-fecha_publicacion']

    def __str__(self):
        return self.titulo

class PQRS(models.Model):
    TIPO_CHOICES = [
        ('peticion',    'Petición'),
        ('queja',       'Queja'),
        ('reclamo',     'Reclamo'),
        ('sugerencia',  'Sugerencia'),
    ]
    ESTADO_CHOICES = [
        ('abierto',    'Abierto'),
        ('en_proceso', 'En Proceso'),
        ('cerrado',    'Cerrado'),
    ]
    cliente   = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='pqrs')
    tipo      = models.CharField(max_length=15, choices=TIPO_CHOICES)
    asunto    = models.CharField(max_length=200)
    descripcion = models.TextField()
    estado    = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='abierto')
    respuesta = models.TextField(blank=True)
    fecha     = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'PQRS'
