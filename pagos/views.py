from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import ComprobantePago
from reservas.models import Reserva


@login_required
def enviar_comprobante(request):
    """Usuario sube un comprobante de pago vinculado a una reserva."""
    reservas_usuario = Reserva.objects.filter(
        usuario=request.user, estado='pendiente'
    )

    if request.method == 'POST':
        imagen      = request.FILES.get('imagen')
        referencia  = request.POST.get('referencia', '').strip()
        banco       = request.POST.get('banco_origen', '').strip()
        monto_str   = request.POST.get('monto', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        reserva_id  = request.POST.get('reserva')

        if not imagen:
            messages.error(request, 'Debes adjuntar la imagen del comprobante.')
            return redirect('enviar_comprobante')

        monto = None
        if monto_str:
            try:
                monto = float(monto_str.replace(',', '.'))
            except ValueError:
                messages.error(request, 'El monto ingresado no es válido.')
                return redirect('enviar_comprobante')

        reserva = None
        if reserva_id:
            try:
                reserva = Reserva.objects.get(id=reserva_id, usuario=request.user)
            except Reserva.DoesNotExist:
                messages.error(request, 'La reserva seleccionada no es válida.')
                return redirect('enviar_comprobante')

        ComprobantePago.objects.create(
            usuario=request.user,
            reserva=reserva,
            imagen=imagen,
            referencia=referencia,
            banco_origen=banco,
            monto=monto,
            descripcion=descripcion,
        )
        messages.success(request, '¡Comprobante enviado! Será revisado por el equipo en breve.')
        return redirect('mis_comprobantes')

    # GET: mostrar formulario y reservas disponibles
    selected_reserva_id = request.GET.get('reserva_id')
    comprobantes = ComprobantePago.objects.filter(usuario=request.user)
    context = {
        'comprobantes':       comprobantes,
        'reservas_usuario':   reservas_usuario,
        'selected_reserva_id': selected_reserva_id,
        'total_pendientes':   comprobantes.filter(estado='pendiente').count(),
        'total_aprobados':    comprobantes.filter(estado='aprobado').count(),
        'total_rechazados':   comprobantes.filter(estado='rechazado').count(),
    }
    return render(request, 'pagos/enviar_comprobante.html', context)


@login_required
def mis_comprobantes(request):
    """Usuario ve el historial de sus comprobantes."""
    comprobantes = ComprobantePago.objects.filter(usuario=request.user)
    context = {
        'comprobantes':     comprobantes,
        'total_pendientes': comprobantes.filter(estado='pendiente').count(),
        'total_aprobados':  comprobantes.filter(estado='aprobado').count(),
        'total_rechazados': comprobantes.filter(estado='rechazado').count(),
    }
    return render(request, 'pagos/mis_comprobantes.html', context)


@user_passes_test(lambda u: u.is_staff)
def admin_comprobantes(request):
    """Admin ve todos los comprobantes con filtros por estado."""
    estado_filtro = request.GET.get('estado', '')
    comprobantes  = ComprobantePago.objects.select_related('usuario', 'reserva').all()

    if estado_filtro:
        comprobantes = comprobantes.filter(estado=estado_filtro)

    total            = ComprobantePago.objects.count()
    total_pendientes = ComprobantePago.objects.filter(estado='pendiente').count()
    total_aprobados  = ComprobantePago.objects.filter(estado='aprobado').count()
    total_rechazados = ComprobantePago.objects.filter(estado='rechazado').count()

    context = {
        'comprobantes':     comprobantes,
        'estado_filtro':    estado_filtro,
        'total':            total,
        'total_pendientes': total_pendientes,
        'total_aprobados':  total_aprobados,
        'total_rechazados': total_rechazados,
    }
    return render(request, 'pagos/admin_comprobantes.html', context)


@user_passes_test(lambda u: u.is_staff)
def admin_revisar_comprobante(request, pk):
    """Admin aprueba, rechaza o deja pendiente un comprobante."""
    comprobante = get_object_or_404(ComprobantePago, pk=pk)

    if request.method == 'POST':
        nuevo_estado = request.POST.get('estado')
        nota_admin   = request.POST.get('nota_admin', '').strip()

        if nuevo_estado in ('aprobado', 'rechazado', 'pendiente'):
            comprobante.estado         = nuevo_estado
            comprobante.nota_admin     = nota_admin
            comprobante.fecha_revision = timezone.now()
            comprobante.save()

            # Si se aprueba, marcar la reserva como confirmada
            if nuevo_estado == 'aprobado' and comprobante.reserva:
                comprobante.reserva.estado = 'confirmada'
                comprobante.reserva.save()
                messages.success(
                    request,
                    f'Comprobante #{pk} APROBADO y Reserva #{comprobante.reserva.id} marcada como CONFIRMADA.'
                )
            elif nuevo_estado == 'rechazado':
                messages.warning(
                    request,
                    f'Comprobante #{pk} marcado como RECHAZADO.'
                )
            else:
                messages.success(
                    request,
                    f'Comprobante #{pk} marcado como {comprobante.get_estado_display()}.'
                )
        else:
            messages.error(request, 'Estado no válido.')

        return redirect('admin_comprobantes')

    context = {'comprobante': comprobante}
    return render(request, 'pagos/admin_revisar_comprobante.html', context)


@user_passes_test(lambda u: u.is_staff)
def admin_eliminar_comprobante(request, pk):
    """Admin elimina un comprobante."""
    if request.method == 'POST':
        comprobante = get_object_or_404(ComprobantePago, pk=pk)
        comprobante.delete()
        messages.info(request, f'Comprobante #{pk} eliminado.')
    return redirect('admin_comprobantes')