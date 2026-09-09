from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone
import json

from App.models import (
    Usuario, Reserva, Paquete, Pago, Promocion, 
    Calificacion, Bitacora, PQRS
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

    now = timezone.now()

    # Métricas consolidadas
    total_invertido = Pago.objects.filter(estado_transaccion__in=['aprobado', 'APROBADO', 'completado']).aggregate(
        total=Sum('monto')
    )['total'] or 0

    total_reservas = Reserva.objects.count()
    reservas_confirmadas = Reserva.objects.filter(estado_reserva__in=['confirmada', 'CONFIRMADA']).count()
    reservas_pendientes = Reserva.objects.filter(estado_reserva__in=['pendiente', 'PENDIENTE']).count()
    reservas_canceladas = Reserva.objects.filter(estado_reserva__in=['cancelada', 'CANCELADA', 'rechazada']).count()
    reservas_completadas = Reserva.objects.filter(estado_reserva__in=['completada', 'COMPLETADA']).count()

    promedio_por_reserva = round(float(total_invertido) / reservas_confirmadas) if reservas_confirmadas > 0 else 0
    destinos_total = Paquete.objects.filter(estado=True).count()
    tasa_exito = round((reservas_confirmadas / total_reservas * 100), 1) if total_reservas > 0 else 0

    # PQRS
    pqrs_abiertas = PQRS.objects.filter(estado__in=['abierto', 'abierta']).count()
    pqrs_en_gestion = PQRS.objects.filter(estado__in=['en_proceso', 'en_gestion']).count()
    pqrs_cerradas = PQRS.objects.filter(estado__in=['cerrado', 'cerrada', 'resuelto']).count()
    pqrs_total = PQRS.objects.count()
    pqrs_tasa_resolucion = round((pqrs_cerradas / pqrs_total * 100), 1) if pqrs_total > 0 else 0

    # Calificaciones
    total_calificaciones = Calificacion.objects.count()
    dias_como_miembro = (now.date() - request.user.date_joined.date()).days if request.user.date_joined else 0

    # Gráficos de evolución mensual (año actual)
    meses_labels = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    meses_datos = [0] * 12
    meses_inversion = [0] * 12

    for r in Reserva.objects.filter(fecha_registro__year=now.year):
        if r.fecha_registro:
            meses_datos[r.fecha_registro.month - 1] += 1

    for p in Pago.objects.filter(fecha_pago__year=now.year, estado_transaccion__in=['aprobado', 'APROBADO', 'completado']):
        if p.fecha_pago:
            meses_inversion[p.fecha_pago.month - 1] += float(p.monto or 0)

    # Gráficos anuales (últimos 3 años)
    anios_labels = [now.year - 2, now.year - 1, now.year]
    anios_datos = [0, 0, 0]
    anios_reservas = [0, 0, 0]
    anios_canceladas = [0, 0, 0]

    for idx, anio in enumerate(anios_labels):
        pagos_anio_val = Pago.objects.filter(
            fecha_pago__year=anio,
            estado_transaccion__in=['aprobado', 'APROBADO', 'completado']
        ).aggregate(s=Sum('monto'))['s'] or 0
        anios_datos[idx] = float(pagos_anio_val)
        anios_reservas[idx] = Reserva.objects.filter(fecha_registro__year=anio).count()
        anios_canceladas[idx] = Reserva.objects.filter(
            fecha_registro__year=anio,
            estado_reserva__in=['cancelada', 'CANCELADA', 'rechazada']
        ).count()

    # Días de la semana (0=Lun..6=Dom)
    dias_datos = [0] * 7
    for r in Reserva.objects.filter(fecha_inicio__isnull=False):
        dias_datos[r.fecha_inicio.weekday()] += 1

    # Top destinos
    destinos_top_labels = []
    destinos_top_datos = []
    destinos_populares = []

    paquetes_top = Paquete.objects.annotate(
        total_res=Count('reservas'),
        inv_total=Sum('reservas__pago__monto', filter=Q(reservas__pago__estado_transaccion__in=['aprobado', 'APROBADO', 'completado']))
    ).order_by('-total_res')[:5]

    for paq in paquetes_top:
        destinos_top_labels.append(paq.nombre)
        destinos_top_datos.append(paq.total_res)
        ultima_reserva = Reserva.objects.filter(paquete=paq).order_by('-fecha_inicio').first()
        destinos_populares.append({
            'nombre': paq.nombre,
            'total_reservas': paq.total_res,
            'inversion_total': float(paq.inv_total or 0),
            'ultima_visita': ultima_reserva.fecha_inicio if ultima_reserva else None
        })

    # Tablas de detalle
    historial_pagos = Pago.objects.select_related('reserva', 'reserva__paquete').order_by('-id')[:10]
    actividad_reciente = Bitacora.objects.select_related('usuario').order_by('-fecha_registro')[:10]

    calificaciones_qs = Calificacion.objects.select_related('reserva', 'reserva__paquete', 'reserva__usuario').order_by('-id')[:10]
    mis_calificaciones = []
    for c in calificaciones_qs:
        mis_calificaciones.append({
            'destino': c.reserva.paquete.nombre if (c.reserva and c.reserva.paquete) else 'Experiencia Mongua',
            'calificacion': c.puntaje_estrellas,
            'puntaje_estrellas': c.puntaje_estrellas,
            'titulo': c.titulo,
            'comentario': c.comentario,
            'publicada': c.visible,
            'visible': c.visible,
            'fecha': c.fecha_calificacion,
            'fecha_calificacion': c.fecha_calificacion
        })

    # Datos para gráfico radar
    radar_datos = [
        min(total_reservas, 100),
        min(int(total_invertido / 100000), 100) if total_invertido else 0,
        min(dias_como_miembro, 100),
        min(total_calificaciones * 10, 100),
        min(int(pqrs_tasa_resolucion), 100),
        min(destinos_total * 10, 100)
    ]

    context = {
        'analitica_titulo': 'Estadísticas Generales de Administración',
        'analitica_subtitulo': 'Consolidado métrico y operativo de todas las reservas, finanzas, PQRS y destinos en Monagua.',
        'admin_mode': True,
        'total_invertido': total_invertido,
        'total_reservas': total_reservas,
        'promedio_por_reserva': promedio_por_reserva,
        'destinos_total': destinos_total,
        'tasa_exito': tasa_exito,
        'pqrs_abiertas': pqrs_abiertas,
        'pqrs_en_gestion': pqrs_en_gestion,
        'pqrs_cerradas': pqrs_cerradas,
        'pqrs_total': pqrs_total,
        'pqrs_tasa_resolucion': pqrs_tasa_resolucion,
        'total_calificaciones': total_calificaciones,
        'total_resenas': total_calificaciones,
        'dias_como_miembro': dias_como_miembro,
        'nivel_viajero': 'Administrador General',
        'descripcion_nivel': 'Acceso y supervisión integral de métricas comerciales y ecológicas del Páramo de Mongua.',
        'progreso_nivel': 100,
        'promedio_mensual_reservas': round(total_reservas / 12, 1) if total_reservas else 0,
        'arboles_conservados': reservas_confirmadas * 3,
        'reservas_confirmadas': reservas_confirmadas,
        'reservas_pendientes': reservas_pendientes,
        'reservas_canceladas': reservas_canceladas,
        'reservas_completadas': reservas_completadas,
        'destinos_populares': destinos_populares,
        'historial_pagos': historial_pagos,
        'actividad_reciente': actividad_reciente,
        'mis_calificaciones': mis_calificaciones,
        'mis_resenas': mis_calificaciones,
        # Variables JSON para Chart.js
        'meses_labels': json.dumps(meses_labels),
        'meses_datos': json.dumps(meses_datos),
        'meses_inversion': json.dumps(meses_inversion),
        'anios_labels': json.dumps(anios_labels),
        'anios_datos': json.dumps(anios_datos),
        'anios_reservas': json.dumps(anios_reservas),
        'anios_canceladas': json.dumps(anios_canceladas),
        'dias_datos': json.dumps(dias_datos),
        'destinos_top_labels': json.dumps(destinos_top_labels),
        'destinos_top_datos': json.dumps(destinos_top_datos),
        'radar_datos': json.dumps(radar_datos),
    }

    return render(request, 'admin/dahsboard/estadisticas_admin.html', context)


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
