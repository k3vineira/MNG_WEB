"""
Utilidades para la creación de notificaciones del sistema.
"""

from .models import Notificacion
from django.contrib.auth.models import User

def crear_notificacion_sistema(usuario, titulo, mensaje, tipo='sistema'):
    """
    Crea una notificación en base de datos para un usuario autenticado.

    Args:
        usuario (User): El objeto de usuario destinatario.
        titulo (str): Título de la notificación.
        mensaje (str): Contenido del mensaje de la notificación.
        tipo (str): Tipo de notificación ('reserva', 'pqrs', 'sistema').

    Returns:
        Notificacion | None: La notificación creada, o None si el usuario no está autenticado.
    """
    if usuario and usuario.is_authenticated:
        return Notificacion.objects.create(
            cliente=usuario,
            titulo=titulo,
            mensaje=mensaje,
            tipo=tipo
        )
    return None
