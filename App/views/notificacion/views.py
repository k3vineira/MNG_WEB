from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from App.models import Notificacion


@login_required(login_url='login')
def listar_notificaciones(request):
    """
    Vista para listar las notificaciones del usuario autenticado.
    """
    notificaciones = Notificacion.objects.filter(usuario=request.user).order_by('-fecha_creacion')
    return render(request, 'partials/notificacion/notificaciones.html', {'notificaciones': notificaciones})


@login_required(login_url='login')
def marcar_notificacion_leida(request, notificacion_id):
    """
    Marca una notificación como leída.
    """
    notificacion = get_object_or_404(Notificacion, id=notificacion_id, usuario=request.user)
    notificacion.leido = True
    notificacion.save()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({'status': 'ok', 'mensaje': 'Notificación marcada como leída'})
    
    return redirect(request.META.get('HTTP_REFERER', 'index'))


@login_required(login_url='login')
def eliminar_notificacion(request, notificacion_id):
    """
    Elimina una notificación del usuario.
    """
    notificacion = get_object_or_404(Notificacion, id=notificacion_id, usuario=request.user)
    notificacion.delete()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        return JsonResponse({'status': 'ok', 'mensaje': 'Notificación eliminada'})
    
    return redirect(request.META.get('HTTP_REFERER', 'index'))
