from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Avg, Q

from App.models import Calificacion, Usuario, Reserva, Paquete


def _es_admin(user):
    """Valida si el usuario actual posee permisos administrativos o rol Administrador."""
    return user.is_authenticated and (user.is_staff or getattr(user, 'rol', None) == Usuario.Roles.ADMIN)


@login_required
def listar_calificaciones_admin(request):
    """Renderiza el módulo de moderación y auditoría de calificaciones para el Staff."""
    if not _es_admin(request.user):
        return redirect('index')

    queryset = Calificacion.objects.all().select_related('reserva', 'reserva__usuario', 'reserva__paquete')
    
    # Manejar filtros
    tipo_filtro = request.GET.get('tipo', '').strip()
    valoracion_filtro = request.GET.get('valoracion', '').strip()
    
    if tipo_filtro:
        queryset = queryset.filter(tipo=tipo_filtro)
    if valoracion_filtro and valoracion_filtro.isdigit():
        queryset = queryset.filter(puntaje_estrellas=int(valoracion_filtro))
        
    calificaciones = queryset.order_by('-fecha_calificacion')
    
    # Calcular estadísticas globales (sin filtros)
    estadisticas = Calificacion.objects.aggregate(
        total=Count('id'),
        total_visibles=Count('id', filter=Q(visible=True)),
        promedio=Avg('puntaje_estrellas')
    )
    
    promedio_val = estadisticas['promedio']
    if promedio_val:
        promedio_val = round(promedio_val, 1)
    else:
        promedio_val = 0

    # Añadir atributos calculados para la vista de estrellas y enlaces
    for c in calificaciones:
        c.estrellas = range(c.puntaje_estrellas or 0)
        c.estrellas_vacias = range(5 - (c.puntaje_estrellas or 0))
        c.usuario = c.reserva.usuario if c.reserva else None
        c.paquete = c.reserva.paquete if c.reserva else None

    return render(request, 'admin/calificacion/calificacion_admin.html', {
        'titulo': 'Gestión de Calificaciones — Administración',
        'calificaciones': calificaciones,
        'total': estadisticas['total'] or 0,
        'total_visibles': estadisticas['total_visibles'] or 0,
        'promedio': promedio_val,
        'tipo_filtro': tipo_filtro,
        'valoracion_filtro': valoracion_filtro
    })


@login_required
def toggle_visible_calificacion(request, pk):
    """Permite al administrador cambiar el estado de visibilidad pública de una calificación."""
    if not _es_admin(request.user):
        return redirect('index')
    
    if request.method == 'POST':
        calificacion = get_object_or_404(Calificacion, pk=pk)
        calificacion.visible = not calificacion.visible
        calificacion.save()
        estado_texto = "visible al público" if calificacion.visible else "oculta"
        messages.success(request, f'La calificación #{calificacion.id} ahora está {estado_texto}.')
    
    return redirect('listar_calificaciones')


@login_required
def responder_calificacion(request, pk):
    """Permite al administrador registrar o actualizar la respuesta oficial a una calificación."""
    if not _es_admin(request.user):
        return redirect('index')
    
    if request.method == 'POST':
        calificacion = get_object_or_404(Calificacion, pk=pk)
        respuesta = request.POST.get('admin_respuesta', '').strip()
        calificacion.admin_respuesta = respuesta
        calificacion.save()
        messages.success(request, f'Respuesta a la calificación #{calificacion.id} guardada exitosamente.')
        
    return redirect('listar_calificaciones')


@login_required
def mis_calificaciones(request):
    """
    Gestiona la visualización y registro de calificaciones realizadas por
    el turista/cliente para sus paquetes y experiencias reservadas.
    """
    # Paquetes con reservas confirmadas para este usuario
    paquetes_reservados = Paquete.objects.filter(
        reservas__usuario=request.user,
        reservas__estado_reserva='confirmada'
    ).distinct()

    if request.method == 'POST':
        tipo = request.POST.get('tipo', 'experiencia').strip()
        titulo = request.POST.get('titulo', '').strip()
        comentario = (request.POST.get('comentario') or request.POST.get('mensaje') or '').strip()
        puntaje_raw = request.POST.get('puntaje_estrellas') or request.POST.get('valoracion', 5)

        # 1. Validación de campos obligatorios
        if not titulo or not comentario:
            messages.error(request, 'El título y el comentario de la experiencia son obligatorios.')
            return redirect('mis_calificaciones')

        # 2. Validación y conversión del puntaje de estrellas (1 a 5)
        try:
            puntaje_int = int(puntaje_raw)
            if puntaje_int < 1 or puntaje_int > 5:
                puntaje_int = 5
        except (ValueError, TypeError):
            puntaje_int = 5

        # 3. Asociación con la reserva confirmada correspondiente
        reserva = None
        tipo_final = tipo

        if tipo.startswith('paquete_'):
            try:
                paquete_id = int(tipo.split('_')[1])
                reserva = Reserva.objects.filter(
                    usuario=request.user,
                    paquete_id=paquete_id,
                    estado_reserva='confirmada'
                ).order_by('-fecha_inicio').first()

                if not reserva:
                    messages.error(request, 'No puedes calificar un paquete que no has reservado y confirmado.')
                    return redirect('mis_calificaciones')

                tipo_final = 'experiencia'
            except (IndexError, ValueError):
                messages.error(request, 'El paquete seleccionado no es válido.')
                return redirect('mis_calificaciones')
        else:
            # Para categorías generales, asociar con la última reserva confirmada del usuario si existe
            reserva = Reserva.objects.filter(
                usuario=request.user,
                estado_reserva='confirmada'
            ).order_by('-fecha_inicio').first()

            if not reserva and not request.user.is_staff:
                messages.error(request, 'Debes tener al menos una reserva confirmada para poder enviar una calificación.')
                return redirect('mis_calificaciones')

        # 4. Creación de la calificación en el modelo Calificacion
        Calificacion.objects.create(
            reserva=reserva,
            tipo=tipo_final,
            titulo=titulo,
            puntaje_estrellas=puntaje_int,
            comentario=comentario,
            visible=True
        )

        messages.success(request, '¡Gracias por tu calificación! Ha sido registrada exitosamente.')
        return redirect('mis_calificaciones')

    # GET: Listado de calificaciones del usuario y de la comunidad
    mis_calificaciones_qs = Calificacion.objects.filter(
        reserva__usuario=request.user
    ).select_related('reserva', 'reserva__paquete', 'reserva__usuario').order_by('-fecha_calificacion')

    calificaciones_publicas_qs = Calificacion.objects.filter(
        visible=True
    ).select_related('reserva', 'reserva__paquete', 'reserva__usuario').order_by('-fecha_calificacion')

    # Decorar elementos para presentación visual de estrellas y metadatos
    for c in mis_calificaciones_qs:
        c.estrellas = range(c.puntaje_estrellas or 0)
        c.estrellas_vacias = range(5 - (c.puntaje_estrellas or 0))
        c.usuario = c.reserva.usuario if c.reserva else None
        c.paquete = c.reserva.paquete if c.reserva else None

    for c in calificaciones_publicas_qs:
        c.estrellas = range(c.puntaje_estrellas or 0)
        c.estrellas_vacias = range(5 - (c.puntaje_estrellas or 0))
        c.usuario = c.reserva.usuario if c.reserva else None
        c.paquete = c.reserva.paquete if c.reserva else None

    # Estadísticas comunitarias
    estadisticas = Calificacion.objects.filter(visible=True).aggregate(
        total=Count('id'),
        promedio=Avg('puntaje_estrellas')
    )

    promedio_val = round(estadisticas['promedio'], 1) if estadisticas['promedio'] else 0

    distribucion = {}
    for i in range(1, 6):
        distribucion[i] = Calificacion.objects.filter(visible=True, puntaje_estrellas=i).count()

    context = {
        'titulo': 'Calificaciones — Monagua',
        'paquetes_reservados': paquetes_reservados,
        'mis_calificaciones': mis_calificaciones_qs,
        'calificaciones_publicas': calificaciones_publicas_qs,
        'stats': {
            'total': estadisticas['total'] or 0,
            'promedio': promedio_val,
        },
        'distribucion': distribucion,
    }

    return render(request, 'usuario/calificacion/calificacion.html', context)

