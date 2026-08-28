"""
Context processor para inyectar notificaciones globales desde el modelo Bitacora.
"""
from App.models import Bitacora

def lista_notificaciones_global(request):
    if request.user.is_authenticated:
        # Trae las últimas 5 notificaciones/bitácoras para la campanita
        alertas = Bitacora.objects.filter(
            usuario=request.user
        ).order_by('-fecha_accion', '-id')[:5]

        # Conteo total de registros del usuario
        contador = Bitacora.objects.filter(
            usuario=request.user
        ).count()

        return {
            'notificaciones_globales': alertas,
            'contador_notificaciones': contador,
        }

    return {
        'notificaciones_globales': [],
        'contador_notificaciones': 0,
    }