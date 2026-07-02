"""
Modelo de datos para las notificaciones del sistema dirigidas a los usuarios.
"""

from django.db import models
from django.conf import settings

class Notificacion(models.Model):
    """
    Notificación generada por el sistema y asociada a un usuario específico.
    Puede ser de tipo reserva, PQRS o sistema general.
    """
    TIPO_CHOICES = [
        ('reserva', 'Reserva'),
        ('pqrs', 'PQRS'),
        ('sistema', 'Sistema'),
    ]

    # Vincula la notificación al usuario conectado
    cliente = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=150)
    mensaje = models.TextField()
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='sistema')
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-fecha_creacion']

    def __str__(self):
        """Retorna el título y el nombre de usuario como representación textual."""
        return f"{self.titulo} - {self.cliente.username}"