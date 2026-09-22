from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum
from App.models import Pago, Reserva
from App.utils import crear_notificacion_sistema

from App.forms.pago.forms import ComprobantePagoForm

@login_required(login_url='login')
def enviar_comprobante(request):
    """
    Vista protegida para que el turista envíe el comprobante de pago de una reserva.
    Aplica validación estricta en el servidor mediante ComprobantePagoForm e impide
    la manipulación del monto, estado o reserva desde el navegador del cliente.
    """
    form = ComprobantePagoForm()

    if request.method == 'POST':
        reserva_id = request.POST.get('reserva')
        if not reserva_id:
            messages.error(request, "Por favor selecciona la reserva a la que corresponde este pago.")
            return redirect('enviar_comprobante')

        # Garantiza que la reserva exista y pertenezca al usuario autenticado (IDOR prevention)
        reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)

        # Evitar pagos duplicados si ya tiene comprobante en revisión o aprobado
        pago_existente = getattr(reserva, 'pago', None)
        if pago_existente and pago_existente.estado_transaccion in ['pendiente', 'aprobado']:
            messages.warning(request, "Esta reserva ya tiene un comprobante registrado o en proceso de revisión.")
            return redirect('mis_comprobantes')

        form = ComprobantePagoForm(request.POST, request.FILES)
        if form.is_valid():
            pago = form.save(commit=False)
            
            # ASIGNACIÓN SEGURA EN SERVIDOR (Zero-Trust Frontend):
            # Si el usuario manipuló el HTML para alterar el monto o estado, se ignora completamente.
            pago.reserva = reserva
            pago.monto = reserva.monto_total
            pago.estado_transaccion = 'pendiente'
            pago.save()

            crear_notificacion_sistema(
                usuario=request.user,
                reserva=reserva,
                mensaje=f"Se ha enviado un nuevo comprobante de pago para la reserva #{reserva.id} del paquete '{reserva.paquete.nombre}'.",
                tipo="Comprobante de Pago",
                prioridad="alta"
            )

            messages.success(request, "¡Tu comprobante de pago ha sido enviado exitosamente y será revisado en breve!")
            return redirect('mis_comprobantes')
        else:
            errores_txt = [str(err[0]) for err in form.errors.values()]
            messages.error(request, f"Error en el comprobante: {' '.join(errores_txt)}")

    selected_reserva_id = request.GET.get('reserva_id', '')
    reservas_elegibles = Reserva.objects.filter(usuario=request.user, estado_reserva='pendiente')
    total_pendientes = Pago.objects.filter(reserva__usuario=request.user, estado_transaccion='pendiente').count()
    total_aprobados = Pago.objects.filter(reserva__usuario=request.user, estado_transaccion='aprobado').aggregate(total=Sum('monto'))['total'] or 0
    total_rechazados = Pago.objects.filter(reserva__usuario=request.user, estado_transaccion='rechazado').count()

    context = {
        'form': form,
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
