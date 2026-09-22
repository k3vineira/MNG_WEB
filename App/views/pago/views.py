from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from App.models import Pago, Reserva
from App.utils import crear_notificacion_sistema

@login_required(login_url='login')
def enviar_comprobante(request):
    """
    Vista para que el turista adjunte y envíe el comprobante de pago de una reserva.
    """
    if request.method == 'POST':
        reserva_id = request.POST.get('reserva')
        referencia = request.POST.get('referencia', '').strip()
        banco_origen = request.POST.get('banco_origen', '').strip()
        monto = request.POST.get('monto', '0')
        metodo_pago = request.POST.get('metodo_pago', 'Transferencia Bancaria').strip()
        imagen_comprobante = request.FILES.get('imagen_comprobante')
        descripcion = request.POST.get('descripcion', '').strip()

        if not reserva_id or not referencia or not banco_origen or not imagen_comprobante:
            messages.error(request, "Por favor completa todos los campos obligatorios y adjunta la imagen del comprobante.")
            return redirect('enviar_comprobante')

        reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)

        # Se ignora cualquier valor de monto recibido en el request y se asigna el monto exacto de la base de datos
        monto_val = reserva.monto_total

        pago = Pago.objects.create(
            reserva=reserva,
            referencia=referencia,
            banco_origen=banco_origen,
            metodo_pago=metodo_pago,
            monto=monto_val,
            imagen_comprobante=imagen_comprobante,
            descripcion=descripcion,
            estado_transaccion='pendiente'
        )

        crear_notificacion_sistema(
            usuario=request.user,
            reserva=reserva,
            mensaje=f"Se ha enviado un nuevo comprobante de pago para la reserva #{reserva.id} del paquete '{reserva.paquete.nombre}'.",
            tipo="Comprobante de Pago",
            prioridad="alta"
        )

        messages.success(request, "¡Tu comprobante de pago ha sido enviado exitosamente y será revisado en breve!")
        return redirect('mis_comprobantes')

    selected_reserva_id = request.GET.get('reserva_id', '')
    reservas_elegibles = Reserva.objects.filter(usuario=request.user, estado_reserva='pendiente')
    total_pendientes = Pago.objects.filter(reserva__usuario=request.user, estado_transaccion='pendiente').count()
    total_aprobados = Pago.objects.filter(reserva__usuario=request.user, estado_transaccion='aprobado').aggregate(total=Sum('monto'))['total'] or 0
    total_rechazados = Pago.objects.filter(reserva__usuario=request.user, estado_transaccion='rechazado').count()

    context = {
        'reservas_elegibles': reservas_elegibles,
        'selected_reserva_id': selected_reserva_id,
        'total_pendientes': total_pendientes,
        'total_aprobados': total_aprobados,
        'total_rechazados': total_rechazados,
    }
    return render(request, 'usuario/pago/enviar_comprobante.html', context)


@login_required(login_url='login')
def mis_comprobantes(request):
    """
    Vista para que el turista consulte el historial y estado de sus comprobantes de pago.
    """
    comprobantes = Pago.objects.filter(reserva__usuario=request.user).select_related('reserva', 'reserva__paquete').order_by('-fecha_envio')
    
    total_pendientes = Pago.objects.filter(reserva__usuario=request.user, estado_transaccion='pendiente').count()
    total_aprobados = Pago.objects.filter(reserva__usuario=request.user, estado_transaccion='aprobado').aggregate(total=Sum('monto'))['total'] or 0
    total_rechazados = Pago.objects.filter(reserva__usuario=request.user, estado_transaccion='rechazado').count()

    context = {
        'comprobantes': comprobantes,
        'total_pendientes': total_pendientes,
        'total_aprobados': total_aprobados,
        'total_rechazados': total_rechazados,
    }
    return render(request, 'usuario/pago/mis_comprobantes.html', context)
