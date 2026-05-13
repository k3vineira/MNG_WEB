from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import Pago

@login_required
def mis_pagos(request):
    """
    Vista que recupera el historial de pagos del usuario actual.
    Aplica DRY al filtrar directamente por la relación del Cliente.
    """
    # Obtenemos los pagos del cliente asociado al usuario logueado
    # select_related('tour') optimiza la carga de los nombres de los paquetes
    pagos = Pago.objects.filter(
        cliente__usuario=request.user
    ).select_related('tour').order_by('-fecha_reserva')

    return render(request, 'private/mis_pagos.html', {
        'pagos': pagos
    })

@login_required
def descargar_recibo(request, pago_id):
    """
    Vista para generar o descargar el comprobante de pago.
    Valida que el pago pertenezca al usuario por seguridad.
    """
    pago = get_object_or_404(Pago, id=pago_id, cliente__usuario=request.user)
    return HttpResponse(f"Generando recibo para el pago #MON-{pago.id} de {pago.tour.nombre}")
