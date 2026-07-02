from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Notificacion

@login_required
def marcar_notificacion_leida(request, noti_id):
    """
    marcar_notificacion_leida.
    
    :param request: marcar notificacion leida.
    
    :param noti_id: ID de la notificación a marcar como leída.
    
    :return: Redirige a la página correspondiente según el tipo de notificación.
    """
    noti = get_object_or_404(Notificacion, id=noti_id, cliente=request.user)
    noti.leida = True
    noti.save()
    
    if noti.tipo == 'reserva':
        return redirect('mis_reservas_usuario')
    elif noti.tipo == 'pqrs':
        return redirect('mis_pqrs')

    return redirect('dashboard_turista')

@login_required
def lista_notificaciones(request):
    """
    lista_notificaciones.
    
    :param request: Solicitud HTTP del usuario autenticado.
    
    :return: Renderiza la plantilla 'historial_completo.html' con las notificaciones del usuario.
    """
    notificaciones = Notificacion.objects.filter(cliente=request.user).order_by('-id')
    return render(request, 'historial_completo.html', {
        'notificaciones': notificaciones
    })