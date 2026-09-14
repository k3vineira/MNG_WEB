from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Sum
from django.utils import timezone
from App.models import Pago, Reserva, Usuario
from App.utils import crear_notificacion_sistema


def es_admin(user):
    """Verifica si el usuario autenticado tiene permisos de administrador."""
    return user.is_authenticated and (user.is_staff or getattr(user, 'rol', None) in [Usuario.Roles.ADMIN, 1, 'ADMIN'])


@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login')
def admin_comprobantes(request):
    """
    Vista administrativa para listar, filtrar y buscar los comprobantes de pago subidos por los usuarios.
    """
    estado_filtro = request.GET.get('estado', '').strip().lower()

    comprobantes = Pago.objects.select_related(
        'reserva', 'reserva__usuario', 'reserva__paquete'
    ).order_by('-fecha_envio')

    if estado_filtro in ['pendiente', 'aprobado', 'rechazado']:
        comprobantes = comprobantes.filter(estado_transaccion=estado_filtro)

    total = Pago.objects.count()
    total_pendientes = Pago.objects.filter(estado_transaccion='pendiente').count()
    total_aprobados = Pago.objects.filter(estado_transaccion='aprobado').aggregate(total=Sum('monto'))['total'] or Decimal('0.00')
    total_rechazados = Pago.objects.filter(estado_transaccion='rechazado').count()

    context = {
        'comprobantes': comprobantes,
        'estado_filtro': estado_filtro,
        'total': total,
        'total_pendientes': total_pendientes,
        'total_aprobados': total_aprobados,
        'total_rechazados': total_rechazados,
    }
    return render(request, 'admin/admin_comprobantes.html', context)


@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login')
def admin_revisar_comprobante(request, pk):
    """
    Vista administrativa para revisar detalladamente un comprobante de pago,
    aprobarlo o rechazarlo, y actualizar sincronizadamente la reserva asociada.
    """
    comprobante = get_object_or_404(
        Pago.objects.select_related('reserva', 'reserva__usuario', 'reserva__paquete'),
        pk=pk
    )
    error_msg = None

    if request.method == 'POST':
        banco_origen = request.POST.get('banco_origen', '').strip()
        monto_str = request.POST.get('monto', '').strip()
        estado_transaccion = request.POST.get('estado_transaccion', '').strip().lower()
        nota_admin = request.POST.get('nota_admin', '').strip()

        if estado_transaccion not in ['pendiente', 'aprobado', 'rechazado']:
            error_msg = "El estado de transacción seleccionado no es válido."
        elif estado_transaccion == 'rechazado' and not nota_admin:
            error_msg = "Debes ingresar una nota del administrador indicando el motivo del rechazo para que el usuario pueda corregirlo."
        else:
            try:
                monto_val = Decimal(monto_str) if monto_str else comprobante.monto
            except (ValueError, TypeError, Decimal.InvalidOperation):
                monto_val = comprobante.monto

            if estado_transaccion == 'aprobado':
                if not banco_origen and not comprobante.banco_origen:
                    error_msg = "Debe especificar el banco o medio de pago de origen para aprobar el comprobante."
                elif not monto_val or monto_val <= 0:
                    error_msg = "Debe especificar un monto pagado válido mayor a cero para aprobar el comprobante."
                elif comprobante.reserva and monto_val < comprobante.reserva.monto_total:
                    error_msg = f"El monto verificado (COP ${monto_val:,.0f}) no puede ser menor al monto total de la reserva (COP ${comprobante.reserva.monto_total:,.0f})."

            if not error_msg:
                estado_anterior = comprobante.estado_transaccion
                comprobante.banco_origen = banco_origen or comprobante.banco_origen
                comprobante.monto = monto_val
                comprobante.estado_transaccion = estado_transaccion
                comprobante.nota_admin = nota_admin
                comprobante.fecha_revision = timezone.now()

                try:
                    comprobante.save()

                    # Actualizar estado de la reserva vinculada
                    if comprobante.reserva:
                        reserva = comprobante.reserva
                        if estado_transaccion == 'aprobado':
                            reserva.estado_reserva = 'confirmada'
                            reserva.save()
                        elif estado_transaccion == 'rechazado' and reserva.estado_reserva == 'confirmada':
                            reserva.estado_reserva = 'pendiente'
                            reserva.save()

                    # Registrar notificación en auditoría / bitácora del sistema
                    crear_notificacion_sistema(
                        usuario=request.user,
                        accion=f"COMPROBANTE {estado_transaccion.upper()}",
                        tabla_afectada="Pagos",
                        observacion=f"El administrador {request.user.username} revisó el comprobante #{comprobante.pk} (Reserva #{comprobante.reserva.id if comprobante.reserva else 'N/A'}).",
                        valor_anterior=f"Estado: {estado_anterior}",
                        nuevo_valor=f"Estado: {estado_transaccion}, Monto: {monto_val}, Nota: {nota_admin or 'Sin notas'}"
                    )

                    messages.success(request, f"¡Comprobante #{comprobante.pk} actualizado como '{estado_transaccion}' correctamente!")
                    return redirect('admin_comprobantes')
                except ValidationError as ve:
                    if hasattr(ve, 'message_dict'):
                        error_msg = " ".join([m for ms in ve.message_dict.values() for m in (ms if isinstance(ms, list) else [ms])])
                    elif hasattr(ve, 'messages'):
                        error_msg = " ".join(ve.messages)
                    else:
                        error_msg = str(ve)

    context = {
        'comprobante': comprobante,
        'error_msg': error_msg,
    }
    return render(request, 'admin/admin_revisar_comprobante.html', context)


@login_required(login_url='login')
@user_passes_test(es_admin, login_url='login')
def admin_eliminar_comprobante(request, pk):
    """
    Vista administrativa para eliminar un comprobante de pago.
    """
    if request.method == 'POST':
        comprobante = get_object_or_404(Pago, pk=pk)
        reserva_id = comprobante.reserva.id if comprobante.reserva else "N/A"
        pago_id = comprobante.pk

        crear_notificacion_sistema(
            usuario=request.user,
            accion="ELIMINAR COMPROBANTE",
            tabla_afectada="Pagos",
            observacion=f"El administrador {request.user.username} eliminó el comprobante #{pago_id} de la reserva #{reserva_id}.",
            valor_anterior=f"Comprobante #{pago_id} (Ref: {comprobante.referencia}, Estado: {comprobante.estado_transaccion})",
            nuevo_valor="Eliminado"
        )

        comprobante.delete()
        messages.success(request, f"El comprobante #{pago_id} ha sido eliminado correctamente.")
    return redirect('admin_comprobantes')
