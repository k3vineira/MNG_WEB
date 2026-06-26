from .models import Notificacion
from django.contrib.auth.models import User

def crear_notificacion_sistema(usuario, titulo, mensaje, tipo='sistema'):
    if usuario and usuario.is_authenticated:
        return Notificacion.objects.create(
            cliente=usuario,
            titulo=titulo,
            mensaje=mensaje,
            tipo=tipo
        )
    return None
