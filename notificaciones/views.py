"""
Vistas para la gestión de notificaciones de usuario.
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Notificacion

@login_required
def marcar_notificacion_leida(request, noti_id):
    """
    Marca una notificación como leída y redirige según su tipo.

    Args:
        request (HttpRequest): Objeto de solicitud HTTP.
        noti_id (int): ID de la notificación a marcar como leída.

    Returns:
        HttpResponseRedirect: Redirige a la vista correspondiente según el tipo de notificación.
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
    Muestra el historial completo de notificaciones del usuario autenticado.

    Args:
        request (HttpRequest): Objeto de solicitud HTTP.

    Returns:
        HttpResponse: Página con la lista de notificaciones del usuario.
    """
    notificaciones = Notificacion.objects.filter(cliente=request.user).order_by('-id')
    return render(request, 'historial_completo.html', {
        'notificaciones': notificaciones
    })