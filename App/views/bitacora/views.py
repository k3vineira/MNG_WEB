from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from App.models import Bitacora


@login_required(login_url='login')
def listar_bitacora(request):
    """
    Vista para listar los registros de bitácora y eventos del sistema.
    Los administradores ven todos los registros y los usuarios sus propias acciones.
    """
    if request.user.is_staff or getattr(request.user, 'rol', None) == 1:
        registros = Bitacora.objects.all().select_related('usuario', 'reserva', 'pago', 'pqrs', 'seguimiento').order_by('-fecha_registro')
    else:
        registros = Bitacora.objects.filter(usuario=request.user).select_related('reserva', 'pago', 'pqrs', 'seguimiento').order_by('-fecha_registro')

    return render(request, 'partials/bitacora/bitacora.html', {'bitacora_registros': registros})


@login_required(login_url='login')
def detalle_bitacora(request, bitacora_id):
    """
    Obtiene los detalles de un registro de bitácora en formato JSON o renderizado.
    """
    if request.user.is_staff or getattr(request.user, 'rol', None) == 1:
        registro = get_object_or_404(Bitacora, id=bitacora_id)
    else:
        registro = get_object_or_404(Bitacora, id=bitacora_id, usuario=request.user)

    data = {
        'id': registro.id,
        'accion': registro.get_accion_display(),
        'modulo': registro.modulo,
        'usuario': registro.usuario.username if registro.usuario else 'Sistema',
        'fecha_registro': registro.fecha_registro.strftime('%d/%m/%Y %H:%M:%S'),
        'ip_origen': registro.ip_origen or '—',
        'registro_id': registro.registro_id or '—',
        'descripcion': registro.descripcion or 'Sin observaciones',
    }
    return JsonResponse({'status': 'ok', 'data': data})
