from .models import Notificacion
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta

def lista_notificaciones_global(request):
    """
    lista_notificaciones_global.
    
    :param request: Descripción del parámetro.
    
    :return: Respuesta de la función.
    """
    if request.user.is_authenticated:
        # Capturar los mensajes activos de Django y guardarlos como notificaciones de base de datos
        storage = messages.get_messages(request)
        messages_list = list(storage)
        
        # Como iteramos el storage, forzamos storage.used = False para que las plantillas front-end
        # de Django/Bootstrap 5 puedan renderizarlos en pantalla en esta misma respuesta.
        storage.used = False
        
        for msg in messages_list:
            tag = msg.tags or ''
            
            # Determinar el título adecuado según el tag del mensaje
            if 'success' in tag:
                titulo = "¡Excelente!"
            elif 'error' in tag or 'danger' in tag:
                titulo = "¡Error!"
            elif 'warning' in tag:
                titulo = "¡Atención!"
            else:
                titulo = "Información"
                
            texto_mensaje = str(msg.message)
            
            # Categorizar según el contenido del mensaje
            texto_lower = texto_mensaje.lower()
            if any(k in texto_lower for k in ['reserva', 'pago', 'comprobante', 'factura']):
                tipo = 'reserva'
            elif any(k in texto_lower for k in ['pqrs', 'solicitud', 'reclamo', 'cancelación']):
                tipo = 'pqrs'
            else:
                tipo = 'sistema'
                
            # Evitar guardar duplicados en peticiones concurrentes o refrescos (rango de 5 segundos)
            recent_limit = timezone.now() - timedelta(seconds=5)
            duplicate_exists = Notificacion.objects.filter(
                cliente=request.user,
                titulo=titulo,
                mensaje=texto_mensaje,
                tipo=tipo,
                fecha_creacion__gte=recent_limit
            ).exists()
            
            if not duplicate_exists:
                Notificacion.objects.create(
                    cliente=request.user,
                    titulo=titulo,
                    mensaje=texto_mensaje,
                    tipo=tipo
                )

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