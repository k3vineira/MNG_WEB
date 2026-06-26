from .models import Notificacion

def lista_notificaciones_global(request):
    if request.user.is_authenticated:
        alertas = Notificacion.objects.filter(cliente=request.user).order_by('-id')[:5]
        contador = Notificacion.objects.filter(cliente=request.user, leida=False).count()
        
        return {
            'notificaciones_globales': alertas,
            'contador_notificaciones': contador
        }
    return {
        'notificaciones_globales': [],
        'contador_notificaciones': 0
    }