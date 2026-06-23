from .models import Notificacion

def lista_notificaciones_global(request):
    if request.user.is_authenticated:
        # Trae las últimas 5 notificaciones en total para la campanita
        alertas = Notificacion.objects.filter(cliente=request.user).order_by('-id')[:5]
        
        # El contador sí debe medir solo las que faltan por leer para mantener el círculo rojo activo
        contador = Notificacion.objects.filter(cliente=request.user, leida=False).count()
        
        return {
            'notificaciones_globales': alertas,
            'contador_notificaciones': contador
        }
    return {
        'notificaciones_globales': [],
        'contador_notificaciones': 0
    }