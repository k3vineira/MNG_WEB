from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
import json

from App.models import (
    Usuario, Reserva, Paquete, Pago, Promocion, 
    Calificacion, Bitacora
)

def _es_admin(user):
    return user.is_authenticated and (user.is_staff or user.rol == Usuario.Roles.ADMIN)


@login_required
def dashboard_admin(request):
    if not _es_admin(request.user):
        return redirect('index')

    now = timezone.now()

    # Métricas principales
    total_usuarios = Usuario.objects.count()
    total_reservas = Reserva.objects.count()
    total_tours = Paquete.objects.count()
    total_promociones = Promocion.objects.count()

    # Reservas por estado
    reservas_confirmadas = Reserva.objects.filter(estado_reserva__in=['confirmada', 'CONFIRMADA', 'completada']).count()
    reservas_pendientes = Reserva.objects.filter(estado_reserva__in=['pendiente', 'PENDIENTE']).count()
    reservas_canceladas = Reserva.objects.filter(estado_reserva__in=['cancelada', 'CANCELADA', 'rechazada']).count()

    # Pagos
    total_ventas = Pago.objects.filter(estado_transaccion__in=['aprobado', 'APROBADO', 'completado']).aggregate(
        total=Sum('monto')
    )['total'] or 0

    total_pagos_rechazados = Pago.objects.filter(estado_transaccion__in=['rechazado', 'RECHAZADO']).count()

    # Gráfica ingresos mensuales (12 meses del año actual)
    ingresos_mensuales = [0] * 12
    pagos_anio = Pago.objects.filter(
        fecha_pago__year=now.year, 
        estado_transaccion__in=['aprobado', 'APROBADO', 'completado']
    )
    for pago in pagos_anio:
        if pago.fecha_pago:
            mes_idx = pago.fecha_pago.month - 1
            ingresos_mensuales[mes_idx] += float(pago.monto or 0)

    # Gráfica reservas esta semana (últimos 7 días)
    reservas_semana = [0] * 7
    # Lun=0..Dom=6
    inicio_semana = now.date() - timezone.timedelta(days=now.weekday())
    for i in range(7):
        dia = inicio_semana + timezone.timedelta(days=i)
        count_dia = Reserva.objects.filter(fecha_registro__date=dia).count()
        reservas_semana[i] = count_dia

    # Actividad reciente (Bitacora o Reservas)
    actividad_reciente = []
    bitacoras = Bitacora.objects.all().order_by('-fecha_registro')[:6]
    for b in bitacoras:
        actividad_reciente.append({
            'texto': f"{b.usuario.username if b.usuario else 'Sistema'}: {b.accion}",
            'tiempo': b.fecha_registro.strftime('%d/%m/%Y %H:%M') if b.fecha_registro else ''
        })

    # Mini stats
    tasa_confirmacion = round((reservas_confirmadas / total_reservas * 100), 1) if total_reservas > 0 else 0
    val_prom = Calificacion.objects.aggregate(avg=Avg('puntaje_estrellas'))['avg'] or 0.0
    valoracion_promedio = round(float(val_prom), 1)
    ingreso_por_reserva = round(total_ventas / reservas_confirmadas) if reservas_confirmadas > 0 else 0

    cancelaciones_hoy = Reserva.objects.filter(
        estado_reserva__in=['cancelada', 'CANCELADA'], 
        fecha_registro__date=now.date()
    ).count()
    cancelaciones_rechazadas = Reserva.objects.filter(estado_reserva__in=['cancelada_rechazada', 'RECHAZADA']).count()
    cancelaciones_pendientes = Reserva.objects.filter(estado_reserva__in=['cancelacion_pendiente', 'PENDIENTE_CANCELACION']).count()

    # Tours populares
    tours_populares = []
    paquetes = Paquete.objects.annotate(num_res=Count('reservas')).order_by('-num_res')[:5]
    max_res = max([p.num_res for p in paquetes], default=1) or 1

    for p in paquetes:
        porcentaje = round((p.num_res / max_res) * 100)
        tours_populares.append({
            'nombre': p.nombre,
            'precio': p.precio_minimo if hasattr(p, 'precio_minimo') else 0,
            'numero_reservas': p.num_res,
            'porcentaje': porcentaje,
        })

    context = {
        'total_ventas': total_ventas,
        'total_usuarios': total_usuarios,
        'total_reservas': total_reservas,
        'total_tours': total_tours,
        'total_pagos_rechazados': total_pagos_rechazados,
        'total_promociones': total_promociones,
        'ingresos_mensuales': json.dumps(ingresos_mensuales),
        'reservas_confirmadas': reservas_confirmadas,
        'reservas_pendientes': reservas_pendientes,
        'reservas_canceladas': reservas_canceladas,
        'actividad_reciente': actividad_reciente,
        'tasa_confirmacion': tasa_confirmacion,
        'valoracion_promedio': valoracion_promedio,
        'ingreso_por_reserva': ingreso_por_reserva,
        'cancelaciones_hoy': cancelaciones_hoy,
        'cancelaciones_rechazadas': cancelaciones_rechazadas,
        'cancelaciones_pendientes': cancelaciones_pendientes,
        'reservas_semana': json.dumps(reservas_semana),
        'tours_populares': tours_populares,
    }

    return render(request, 'admin/dahsboard/Dashboard-admin.html', context)


@login_required
def estadisticas_admin(request):
    if not _es_admin(request.user):
        return redirect('index')
    return render(request, 'admin/dahsboard/estadisticas_admin.html')


@login_required
def perfil_admin(request):
    if not _es_admin(request.user):
        return redirect('index')

    user = request.user
    if request.method == 'POST' and request.POST.get('editar_perfil') == '1':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        imagen_perfil = request.FILES.get('imagen_perfil')

        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if telefono:
            user.telefono = telefono
        if imagen_perfil:
            user.imagen_perfil = imagen_perfil

        user.save()
        messages.success(request, 'Perfil actualizado correctamente.')
        return redirect('admin_perfil')

    return render(request, 'admin/dahsboard/perfil_admin.html', {'user': user})
