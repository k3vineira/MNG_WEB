from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .models import ComprobantePago
from reservas.models import Reserva, Cancelacion
from django.db.models import Q, OuterRef, Subquery


@login_required
def enviar_comprobante(request):
    """Usuario sube un comprobante de pago vinculado a una reserva o multa."""
    penalidad_subquery = Cancelacion.objects.filter(
        reserva=OuterRef('pk'),
        estado='aceptada'
    ).values('penalidad')[:1]

    reservas_usuario = Reserva.objects.filter(usuario=request.user).filter(
        Q(estado='pendiente') |
        Q(estado='cancelada', cancelaciones__estado='aceptada',
          cancelaciones__penalidad__gt=0)
    ).annotate(
        multa=Subquery(penalidad_subquery)
    ).distinct()

    if request.method == 'POST':
        imagen = request.FILES.get('imagen')
        referencia = request.POST.get('referencia', '').strip()
        banco = request.POST.get('banco_origen', '').strip()
        descripcion = request.POST.get('descripcion', '').strip()
        reserva_id = request.POST.get('reserva')

        if not imagen or not referencia or not banco or not reserva_id:
            messages.error(
                request, 'Todos los campos obligatorios (*) deben ser completados.')
            return redirect('enviar_comprobante')

        reserva = None
        try:
            reserva = Reserva.objects.get(
                id=reserva_id, usuario=request.user)
        except Reserva.DoesNotExist:
            messages.error(
                request, 'La reserva seleccionada no es válida.')
            return redirect('enviar_comprobante')

        # Determinar el monto fijo de la reserva o multa
        if reserva.estado == 'cancelada':
            cancellation = Cancelacion.objects.filter(reserva=reserva, estado='aceptada').first()
            monto = cancellation.penalidad if cancellation else 0
        else:
            monto = reserva.monto_total

        ComprobantePago.objects.create(
            usuario=request.user,
            reserva=reserva,
            imagen=imagen,
            referencia=referencia,
            banco_origen=banco,
            monto=monto,
            descripcion=descripcion,
        )
        messages.success(
            request, '¡Comprobante enviado! Será revisado por el equipo en breve.')
        return redirect('mis_comprobantes')

    # GET: mostrar formulario y reservas disponibles
    selected_reserva_id = request.GET.get('reserva_id')
    comprobantes = ComprobantePago.objects.filter(usuario=request.user)
    from django.db.models import Sum
    context = {
        'comprobantes':       comprobantes,
        'reservas_usuario':   reservas_usuario,
        'selected_reserva_id': selected_reserva_id,
        'total_pendientes':   comprobantes.filter(estado='pendiente').count(),
        'total_aprobados':    comprobantes.filter(estado='aprobado').aggregate(total=Sum('monto'))['total'] or 0,
        'total_rechazados':   comprobantes.filter(estado='rechazado').count(),
    }
    return render(request, 'pagos/enviar_comprobante.html', context)


@login_required
def mis_comprobantes(request):
    """Usuario ve el historial de sus comprobantes."""
    comprobantes = ComprobantePago.objects.filter(usuario=request.user)
    from django.db.models import Sum
    context = {
        'comprobantes':     comprobantes,
        'total_pendientes': comprobantes.filter(estado='pendiente').count(),
        'total_aprobados':  comprobantes.filter(estado='aprobado').aggregate(total=Sum('monto'))['total'] or 0,
        'total_rechazados': comprobantes.filter(estado='rechazado').count(),
    }
    return render(request, 'pagos/mis_comprobantes.html', context)


@user_passes_test(lambda u: u.is_staff)
def admin_comprobantes(request):
    """Admin ve todos los comprobantes con filtros por estado."""
    estado_filtro = request.GET.get('estado', '')
    comprobantes = ComprobantePago.objects.select_related(
        'usuario', 'reserva').all()

    if estado_filtro:
        comprobantes = comprobantes.filter(estado=estado_filtro)
    else:
        # Excluir rechazados de la vista general
        comprobantes = comprobantes.exclude(estado='rechazado')

    total = ComprobantePago.objects.count()
    total_pendientes = ComprobantePago.objects.filter(
        estado='pendiente').count()
    from django.db.models import Sum
    total_aprobados = ComprobantePago.objects.filter(
        estado='aprobado').aggregate(total=Sum('monto'))['total'] or 0
    total_rechazados = ComprobantePago.objects.filter(
        estado='rechazado').count()

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
        nota_admin = request.POST.get('nota_admin', '').strip()

        if nuevo_estado in ('aprobado', 'rechazado', 'pendiente'):
            comprobante.estado = nuevo_estado
            comprobante.nota_admin = nota_admin
            comprobante.fecha_revision = timezone.now()
            comprobante.save()

            # Si se aprueba, marcar la reserva como confirmada (solo si no estaba cancelada por multa)
            if nuevo_estado == 'aprobado' and comprobante.reserva:
                if comprobante.reserva.estado != 'cancelada':
                    comprobante.reserva.estado = 'confirmada'
                    comprobante.reserva.save()
                    messages.success(
                        request,
                        f'Comprobante #{pk} APROBADO y Reserva #{comprobante.reserva.id} marcada como CONFIRMADA.'
                    )
                else:
                    messages.success(
                        request,
                        f'Comprobante #{pk} APROBADO para el pago de la multa de la Reserva #{comprobante.reserva.id}.'
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

    # PÁGINA DE PAGOS RECHAZADOS Y CANCELACIONES RECHAZADAS


@login_required
def mis_rechazos(request):
    if request.user.is_staff:
        return redirect('dashboard')

    try:
        from pagos.models import ComprobantePago
        pagos_rechazados = ComprobantePago.objects.filter(
            usuario=request.user,
            estado='rechazado'
        ).select_related('reserva__paquete').order_by('-fecha_revision')
    except ImportError:
        pagos_rechazados = []

    try:
        from reservas.models import Cancelacion
        cancelaciones_rechazadas = Cancelacion.objects.filter(
            reserva__usuario=request.user,
            estado='rechazada'
        ).select_related('reserva__paquete').order_by('-id')
    except ImportError:
        cancelaciones_rechazadas = []

    total_pagos_rechazados = len(pagos_rechazados) if isinstance(pagos_rechazados, list) else pagos_rechazados.count()
    total_cancelaciones_rechazadas = len(cancelaciones_rechazadas) if isinstance(cancelaciones_rechazadas, list) else cancelaciones_rechazadas.count()

    context = {
        'pagos_rechazados': pagos_rechazados,
        'cancelaciones_rechazadas': cancelaciones_rechazadas,
        'total_pagos_rechazados': total_pagos_rechazados,
        'total_cancelaciones_rechazadas': total_cancelaciones_rechazadas,
    }

    return render(request, 'private/rechazos.html', context)
