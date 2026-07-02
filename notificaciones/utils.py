from .models import Notificacion
from django.contrib.auth.models import User

def crear_notificacion_sistema(usuario, titulo, mensaje, tipo='sistema'):
    """
    crear_notificacion_sistema.
    
    :param usuario: Descripción del parámetro.
    
    :param titulo: Descripción del parámetro.
    
    :param mensaje: Descripción del parámetro.
    
    :param tipo='sistema': Descripción del parámetro.
    
    :return: Respuesta de la función.
    """
    if usuario and usuario.is_authenticated:
        return Notificacion.objects.create(
            cliente=usuario,
            titulo=titulo,
            mensaje=mensaje,
            tipo=tipo
        )
    return None
