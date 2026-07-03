"""
Modelos de datos para la comunidad: Calificaciones, Blog, PQRS y Comentarios.
"""

from django.db import models
from django.urls import reverse


# Create your models here.


class Calificacion(models.Model):
    """
    Calificación de un paquete turístico realizada por un cliente.
    Solo se permite una calificación por cliente y paquete.
    """
    cliente = models.ForeignKey('usuarios.Cliente', on_delete=models.CASCADE)
    paquete = models.ForeignKey('catalogo.Paquete', on_delete=models.CASCADE)
    puntaje = models.PositiveSmallIntegerField()
    comentario = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('cliente', 'paquete')


class Blog(models.Model):
    """
    Entrada de blog publicada por el equipo de Monagua.
    """
    titulo = models.CharField(max_length=200)
    contenido = models.TextField()
    informacion_adicional = models.TextField(blank=True)
    imagen = models.ImageField(upload_to='blog/', blank=True, null=True)
    fecha_publicacion = models.DateTimeField(auto_now_add=True)
    publicado = models.BooleanField(
        default=True, verbose_name='¿Está Publicado?')

    class Meta:
        ordering = ['-fecha_publicacion']

    def get_absolute_url(self):
        """Retorna la URL de detalle de este post del blog."""
        return reverse('detalle_blog', kwargs={'id': self.id})

    def __str__(self):
        """Retorna el título del blog como representación textual."""
        return self.titulo


class PQRS(models.Model):
    """
    Solicitud de Petición, Queja, Reclamo o Sugerencia enviada por un usuario.
    """
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
    cliente = models.ForeignKey(
        'usuarios.Cliente', on_delete=models.CASCADE, related_name='pqrs', null=True, blank=True)
    tipo = models.CharField(max_length=15, choices=TIPO_CHOICES)
    asunto = models.CharField(max_length=200)
    descripcion = models.TextField()
    estado = models.CharField(
        max_length=15, choices=ESTADO_CHOICES, default='abierto')
    respuesta = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'PQRS'


class Comentario(models.Model):
    """Comentarios y reseñas de experiencias de usuarios."""
    usuario = models.ForeignKey(
        'usuarios.Usuario',
        on_delete=models.CASCADE,
        related_name='comentarios',
        verbose_name='Usuario'
    )
    tipo = models.CharField(
        max_length=20,
        default='experiencia',
        verbose_name='Tipo',
        help_text='Tipo de comentario: experiencia, pregunta, etc.'
    )
    titulo = models.CharField(
        max_length=255, blank=True, verbose_name='Título')
    mensaje = models.TextField(verbose_name='Mensaje')
    valoracion = models.PositiveSmallIntegerField(
        default=5, verbose_name='Valoración')
    paquete = models.ForeignKey(
        'catalogo.Paquete',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='comentarios',
        verbose_name='Paquete'
    )
    visible = models.BooleanField(default=True, verbose_name='¿Visible?')
    admin_respuesta = models.TextField(
        blank=True, null=True, verbose_name='Respuesta del Admin')
    fecha_creacion = models.DateTimeField(
        auto_now_add=True, verbose_name='Fecha de Creación')

    class Meta:
        ordering = ['-fecha_creacion']
        verbose_name = 'Comentario'
        verbose_name_plural = 'Comentarios'

    def __str__(self):
        """Retorna el usuario y título del comentario como representación textual."""
        return f"Comentario de {self.usuario.username} - {self.titulo or 'sin título'}"

