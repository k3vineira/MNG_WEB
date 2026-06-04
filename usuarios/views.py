from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from .models import Usuario, Cliente, Comentario
from .forms import RegistroForm, PerfilUsuarioForm


@login_required
def index_turista(request):
    # if request.user.is_staff:
    #     return redirect('dashboard')
    context = {'titulo': 'Bienvenido a Monagua'}
    return render(request, 'index_turista.html', context)


@user_passes_test(lambda u: u.is_staff, login_url='inicio')
def dashboard_admin(request):
    from reservas.models import Reserva, Cancelacion
    from catalogo.models import Paquete
    from django.db.models import Sum, Count, Avg
    from django.utils.timesince import timesince
    from datetime import timedelta

    hoy = timezone.now().date()
    anio_actual = hoy.year

    try:
        total_usuarios = Usuario.objects.filter(is_staff=False).count()
    except:
        total_usuarios = 0

    try:
        total_tours = Paquete.objects.filter(estado=True).count()
    except:
        total_tours = 0

    total_reservas = total_ventas = reservas_confirmadas = 0
    reservas_pendientes = reservas_canceladas = tasa_confirmacion = 0
    ingreso_por_reserva = cancelaciones_hoy = 0
    total_pagos_rechazados = cancelaciones_pendientes = cancelaciones_rechazadas = 0
    valoracion_promedio = 0.0
    ingresos_mensuales = [0] * 12
    reservas_semana = [0] * 7
    tours_populares = []
    max_reservas = 1
    actividad_reciente = []

    try:
        from reservas.models import Reserva, Cancelacion
        total_reservas = Reserva.objects.count()
        try:
            total_ventas = Reserva.objects.filter(
                estado='confirmada'
            ).aggregate(total=Sum('monto_total'))['total'] or 0
            reservas_confirmadas = Reserva.objects.filter(estado='confirmada').count()
            reservas_pendientes  = Reserva.objects.filter(estado='pendiente').count()
            reservas_canceladas  = Reserva.objects.filter(estado='cancelada').count()
            if total_reservas > 0:
                tasa_confirmacion = round((reservas_confirmadas / total_reservas) * 100)
            if reservas_confirmadas > 0:
                ingreso_por_reserva = round(total_ventas / reservas_confirmadas)
            for i, mes in enumerate(range(1, 13)):
                total_mes = Reserva.objects.filter(
                    estado='confirmada', fecha__year=anio_actual, fecha__month=mes
                ).aggregate(total=Sum('monto_total'))['total'] or 0
                ingresos_mensuales[i] = float(total_mes)
            
            from pagos.models import ComprobantePago
            total_pagos_rechazados = ComprobantePago.objects.filter(estado='rechazado').count()
            cancelaciones_pendientes = Cancelacion.objects.filter(estado='revision').count()
            cancelaciones_rechazadas = Cancelacion.objects.filter(estado='rechazada').count()
            
            from .models import Comentario
            valoracion_promedio = round(Comentario.objects.filter(visible=True).aggregate(promedio=Avg('valoracion'))['promedio'] or 0.0, 1)
        except Exception as e:
            print(f"[Dashboard] Error: {e}")
        try:
            from datetime import timedelta
            for i, dias in enumerate(range(6, -1, -1)):
                dia = hoy - timedelta(days=dias)
                reservas_semana[i] = Reserva.objects.filter(fecha=dia).count()
        except:
            pass
        try:
            cancelaciones_hoy = Cancelacion.objects.filter(reserva__fecha=hoy).count()
        except:
            pass
        try:
            tours_populares = list(Paquete.objects.annotate(
                numero_reservas=Count('reserva')
            ).order_by('-numero_reservas')[:5])
            max_reservas = tours_populares[0].numero_reservas if tours_populares and tours_populares[0].numero_reservas > 0 else 1
        except:
            pass
        try:
            ultimas = Reserva.objects.select_related('usuario', 'paquete').order_by('-id')[:8]
            for r in ultimas:
                nombre = r.usuario.get_full_name() or r.usuario.username
                try:
                    estado_txt = r.get_estado_display()
                except:
                    estado_txt = 'Sin estado'
                actividad_reciente.append({
                    'texto': f"{nombre} reservó '{r.paquete.nombre}' — {estado_txt}",
                    'tiempo': timesince(r.fecha) + ' atrás',
                })
        except:
            pass
    except Exception as e:
        print(f"[Dashboard] Error importando Reserva: {e}")

    context = {
        'titulo':               'Tablero de Rendimiento',
        'total_ventas':         total_ventas,
        'total_usuarios':       total_usuarios,
        'total_reservas':       total_reservas,
        'total_tours':          total_tours,
        'total_promociones':    0,
        'ingresos_mensuales':   ingresos_mensuales,
        'reservas_confirmadas': reservas_confirmadas,
        'reservas_pendientes':  reservas_pendientes,
        'reservas_canceladas':  reservas_canceladas,
        'reservas_semana':      reservas_semana,
        'tasa_confirmacion':    tasa_confirmacion,
        'valoracion_promedio':  valoracion_promedio,
        'ingreso_por_reserva':  ingreso_por_reserva,
        'cancelaciones_hoy':    cancelaciones_hoy,
        'total_pagos_rechazados': total_pagos_rechazados,
        'cancelaciones_pendientes': cancelaciones_pendientes,
        'cancelaciones_rechazadas': cancelaciones_rechazadas,
        'tours_populares':      tours_populares,
        'max_reservas':         max_reservas,
        'actividad_reciente':   actividad_reciente,
    }
    return render(request, 'admin/index-admin.html', context)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('inicio')
    if request.method == 'POST':
        data = request.POST.copy()
        username_input = data.get('username')
        if username_input and '@' in username_input:
            user_obj = Usuario.objects.filter(email=username_input).first()
            if user_obj:
                data['username'] = user_obj.username
        form = AuthenticationForm(request, data=data)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                auth_login(request, user)
                messages.success(request, f"¡Bienvenido de nuevo, {user.username}!")
                # Redirect tourists to their landing page after login
                if hasattr(user, 'rol') and user.rol == Usuario.Roles.CLIENTE:
                    return redirect('index_turista')
                next_url = request.GET.get('next')
                if next_url:
                    paquete_id = request.GET.get('paquete_id')
                    if paquete_id:
                        next_url = f"{next_url}?paquete_id={paquete_id}"
                    return redirect(next_url)
                return redirect('inicio')
    else:
        form = AuthenticationForm()
    return render(request, 'authentication/login.html', {'form': form})



def logout_view(request):
    auth_logout(request)
    messages.info(request, "Has cerrado sesión exitosamente.")
    return redirect('login')


def registro_view(request):
    if request.user.is_authenticated:
        return redirect('inicio')
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.rol = Usuario.Roles.CLIENTE
            pais = request.POST.get('pais', '')
            ciudad = request.POST.get('ciudad', '')
            if pais and ciudad:
                user.residencia = f"{ciudad}, {pais}"
            user.save()
            Cliente.objects.create(usuario=user, pais=pais, ciudad=ciudad)
            # Auto-login the new tourist user
            from django.contrib.auth import login as auth_login
            auth_login(request, user)
            messages.success(request, "¡Registro exitoso! Bienvenido.")
            return redirect('index_turista')
        else:
            messages.error(request, "Hubo un error en el registro. Por favor, revisa los datos.")
    else:
        form = RegistroForm()
    return render(request, 'authentication/registro.html', {'form': form})


def terminos_view(request):
    return render(request, 'public/terminos.html')


def nosotros_view(request):
    return render(request, 'public/nosotros.html')


@login_required
def perfil_view(request):
    user = request.user
    if request.method == 'POST':
        if 'imagen_perfil' in request.FILES:
            user.imagen_perfil = request.FILES['imagen_perfil']
            user.save()
            messages.success(request, "¡Foto de perfil actualizada con éxito!")
            return redirect('detalles')
            
        elif request.POST.get('editar_perfil') == '1':
            form = PerfilUsuarioForm(request.POST, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, '¡Información actualizada correctamente!')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field.replace('_', ' ').capitalize()}: {error}")
        return redirect('detalles')
    return render(request, 'private/perfil_turista.html')


@user_passes_test(lambda u: u.is_staff)
def gestion_guias(request, id=None):
    all_users = Usuario.objects.all().order_by('-date_joined')
    guias     = Usuario.objects.filter(es_guia=True)
    guia_sel  = get_object_or_404(Usuario, id=id) if id else None
    context = {
        'fecha':                 timezone.now().strftime('%d %b, %Y'),
        'guias':                 guias,
        'total_guias':           guias.count(),
        'total_guias_activos':   guias.filter(is_active=True).count(),
        'guias_asignados':       0,
        'total_guias_inactivos': guias.filter(is_active=False).count(),
        'all_users':             all_users,
        'total_users':           all_users.count(),
        'guia_sel':              guia_sel,
    }
    return render(request, 'admin/index-guias.html', context)


@user_passes_test(lambda u: u.is_staff)
def asignar_rol_guia(request, user_id):
    if request.method == 'POST':
        user_obj = get_object_or_404(Usuario, id=user_id)
        user_obj.es_guia = not user_obj.es_guia
        user_obj.save()
        accion = "asignado como" if user_obj.es_guia else "removido de"
        messages.success(request, f"Usuario {user_obj.username} {accion} guía.")
    return redirect('gestion_guias')


@user_passes_test(lambda u: u.is_staff)
def guias_baja_reactivar(request, id, estado):
    if request.method == 'POST':
        guia = get_object_or_404(Usuario, id=id)
        guia.is_active = (estado == 'activar')
        guia.save()
        msg = "reactivado" if guia.is_active else "dado de baja"
        messages.info(request, f"Guía {guia.first_name} {msg} exitosamente.")
    return redirect('gestion_guias')


@user_passes_test(lambda u: u.is_staff)
def guias_guardar(request):
    if request.method == 'POST':
        messages.success(request, "Datos del guía guardados correctamente.")
    return redirect('gestion_guias')


# ── Comentarios ──────────────────────────────────────────────────────────────

@login_required
def enviar_comentario(request):
    from catalogo.models import Paquete
    if request.method == 'POST':
        tipo       = request.POST.get('tipo', 'experiencia')
        titulo     = request.POST.get('titulo', '').strip()
        mensaje    = request.POST.get('mensaje', '').strip()
        try:
            valoracion = max(1, min(5, int(request.POST.get('valoracion', 5))))
        except (ValueError, TypeError):
            valoracion = 5

        paquete = None
        if tipo.startswith('paquete_'):
            try:
                paquete_id = int(tipo.split('_')[1])
                paquete = Paquete.objects.filter(id=paquete_id).first()
                tipo = 'experiencia'
            except (ValueError, IndexError):
                pass

        if titulo and mensaje:
            Comentario.objects.create(
                usuario=request.user,
                tipo=tipo,
                titulo=titulo,
                mensaje=mensaje,
                valoracion=valoracion,
                paquete=paquete,
            )
            messages.success(request, '¡Tu comentario fue enviado correctamente!')
        else:
            messages.error(request, 'Por favor completa todos los campos.')
        return redirect('mis_resenas')

    mis_comentarios = Comentario.objects.filter(
        usuario=request.user
    ).select_related('paquete').order_by('-fecha_creacion')[:5]

    comentarios_publicos = Comentario.objects.filter(
        visible=True
    ).select_related('usuario', 'paquete').exclude(usuario=request.user).order_by('-fecha_creacion')[:10]

    paquetes_activos = Paquete.objects.filter(estado=True)
    context = {
        'mis_comentarios':      mis_comentarios,
        'comentarios_publicos': comentarios_publicos,
        'paquetes_activos':     paquetes_activos,
    }
    return render(request, 'private/comentarios.html', context)


@user_passes_test(lambda u: u.is_staff)
def listar_comentarios(request):
    from django.db.models import Avg
    tipo_filtro       = request.GET.get('tipo', '')
    valoracion_filtro = request.GET.get('valoracion', '')
    comentarios = Comentario.objects.select_related('usuario', 'paquete').all()
    if tipo_filtro:
        comentarios = comentarios.filter(tipo=tipo_filtro)
    if valoracion_filtro:
        comentarios = comentarios.filter(valoracion=valoracion_filtro)
    total          = comentarios.count()
    total_visibles = comentarios.filter(visible=True).count()
    agg = comentarios.aggregate(avg=Avg('valoracion'))
    promedio = round(agg['avg'] or 0, 1)
    context = {
        'comentarios':        comentarios,
        'total':              total,
        'total_visibles':     total_visibles,
        'promedio':           promedio,
        'tipo_filtro':        tipo_filtro,
        'valoracion_filtro':  valoracion_filtro,
    }
    return render(request, 'admin/comentarios.html', context)


@user_passes_test(lambda u: u.is_staff)
def toggle_visible(request, pk):
    if request.method == 'POST':
        comentario = get_object_or_404(Comentario, pk=pk)
        comentario.visible = not comentario.visible
        comentario.save()
        estado = 'visible' if comentario.visible else 'oculto'
        messages.success(request, f'Comentario marcado como {estado}.')
    return redirect('listar_comentarios')

@login_required
def mis_resenas_view(request):
    from django.db.models import Avg, Count
    from catalogo.models import Paquete

    # ── POST: crear nueva reseña ─────────────────────────────────────────
    if request.method == 'POST':
        tipo       = request.POST.get('tipo', 'experiencia')
        titulo     = request.POST.get('titulo', '').strip()
        mensaje    = request.POST.get('mensaje', '').strip()
        valoracion = request.POST.get('valoracion', '5')
        try:
            valoracion = max(1, min(5, int(valoracion)))
        except (ValueError, TypeError):
            valoracion = 5

        paquete = None
        if tipo.startswith('paquete_'):
            try:
                paquete_id = int(tipo.split('_')[1])
                paquete = Paquete.objects.filter(id=paquete_id).first()
                tipo = 'experiencia'
            except (ValueError, IndexError):
                pass

        if titulo and mensaje:
            Comentario.objects.create(
                usuario=request.user,
                tipo=tipo,
                titulo=titulo,
                mensaje=mensaje,
                valoracion=valoracion,
                paquete=paquete,
            )
            messages.success(request, '¡Tu reseña fue enviada correctamente!')
        else:
            messages.error(request, 'Por favor completa todos los campos.')
        return redirect('mis_resenas')

    # ── GET: mostrar reseñas ─────────────────────────────────────────────
    mis_resenas = Comentario.objects.filter(
        usuario=request.user
    ).select_related('paquete').order_by('-fecha_creacion')[:10]

    resenas_publicas = Comentario.objects.filter(
        visible=True
    ).select_related('usuario', 'paquete').order_by('-fecha_creacion')[:20]

    # Estadísticas
    todas = Comentario.objects.filter(visible=True)
    agg = todas.aggregate(total=Count('id'), promedio=Avg('valoracion'))
    stats = {
        'total':    agg['total'] or 0,
        'promedio': round(agg['promedio'] or 0, 1),
    }

    # Distribución de estrellas (1-5)
    distribucion = {}
    if stats['total'] > 0:
        dist_qs = todas.values('valoracion').annotate(cnt=Count('id'))
        for row in dist_qs:
            distribucion[row['valoracion']] = row['cnt']

    paquetes_activos = Paquete.objects.filter(estado=True)

    context = {
        'mis_resenas':       mis_resenas,
        'resenas_publicas':  resenas_publicas,
        'stats':             stats,
        'distribucion':      distribucion,
        'paquetes_activos':  paquetes_activos,
    }
    return render(request, 'private/resenas.html', context)

@login_required
def estadisticas_usuario(request):
    import json
    from django.utils import timezone
    from django.db.models import Sum, Avg, Count, Max, Q
    from reservas.models import Reserva
    from pagos.models import ComprobantePago
    from comunidad.models import PQRS
    from .models import Comentario, Cliente

    is_admin = request.user.is_staff
    now = timezone.now()

    if is_admin:
        # 1. Global Statistics (Admin)
        total_reservas = Reserva.objects.count()
        reservas_confirmadas = Reserva.objects.filter(estado='confirmada').count()
        reservas_pendientes = Reserva.objects.filter(estado='pendiente').count()
        reservas_canceladas = Reserva.objects.filter(estado='cancelada').count()
        reservas_completadas = Reserva.objects.filter(estado='completada').count()

        total_invertido = ComprobantePago.objects.filter(estado='aprobado').aggregate(total=Sum('monto'))['total'] or 0.0
        pagos_pendientes = ComprobantePago.objects.filter(estado='pendiente').count()
        pagos_rechazados = ComprobantePago.objects.filter(estado='rechazado').count()
        total_comprobantes = ComprobantePago.objects.count()

        reservas_pagadas = reservas_confirmadas + reservas_completadas
        promedio_por_reserva = float(total_invertido) / reservas_pagadas if reservas_pagadas > 0 else 0.0

        total_comentarios = Comentario.objects.count()
        promedio_calificacion = Comentario.objects.aggregate(promedio=Avg('valoracion'))['promedio'] or 0.0

        distribucion_calificaciones = []
        for estrellas in range(5, 0, -1):
            cant = Comentario.objects.filter(valoracion=estrellas).count()
            porcentaje = round((cant / total_comentarios * 100)) if total_comentarios > 0 else 0
            distribucion_calificaciones.append({
                'estrellas': estrellas,
                'cantidad': cant,
                'porcentaje': porcentaje
            })

        total_pqrs = PQRS.objects.count()
        pqrs_abiertas = PQRS.objects.filter(estado='abierto').count()
        pqrs_en_gestion = PQRS.objects.filter(estado='en_proceso').count()
        pqrs_cerradas = PQRS.objects.filter(estado='cerrado').count()
        pqrs_sin_respuesta = PQRS.objects.filter(Q(respuesta=None) | Q(respuesta='')).count()

        destinos_qs = Reserva.objects.values('paquete__nombre')\
            .annotate(total_reservas=Count('id'), ultima_visita=Max('fecha'))\
            .order_by('-total_reservas')[:5]
        
        destinos_frecuentes = []
        for item in destinos_qs:
            destinos_frecuentes.append({
                'nombre': item['paquete__nombre'],
                'total_reservas': item['total_reservas'],
                'ultima_visita': item['ultima_visita']
            })

        # Recent activity (global)
        reservas_recientes = Reserva.objects.select_related('usuario', 'paquete').order_by('-fecha_registro')[:5]
        pagos_recientes = ComprobantePago.objects.select_related('usuario').order_by('-fecha_envio')[:5]
        comentarios_recientes = Comentario.objects.select_related('usuario').order_by('-fecha_creacion')[:5]
        pqrs_recientes = PQRS.objects.select_related('cliente__usuario').order_by('-fecha')[:5]

        actividades = []
        for res in reservas_recientes:
            usr_name = res.usuario.get_full_name() or res.usuario.username
            actividades.append({
                'tipo': 'reserva',
                'descripcion': f"{usr_name} reservó '{res.paquete.nombre}'",
                'fecha': res.fecha_registro,
                'monto': None
            })
        for comp in pagos_recientes:
            usr_name = comp.usuario.get_full_name() or comp.usuario.username
            actividades.append({
                'tipo': 'pago',
                'descripcion': f"{usr_name} envió comprobante ({comp.get_estado_display()})",
                'fecha': comp.fecha_envio,
                'monto': comp.monto
            })
        for comment in comentarios_recientes:
            usr_name = comment.usuario.get_full_name() or comment.usuario.username
            actividades.append({
                'tipo': 'resena',
                'descripcion': f"{usr_name} calificó con {comment.valoracion}★: '{comment.titulo}'",
                'fecha': comment.fecha_creacion,
                'monto': None
            })
        for pqr in pqrs_recientes:
            usr_name = pqr.cliente.usuario.get_full_name() if pqr.cliente else "Anónimo"
            actividades.append({
                'tipo': 'pqrs',
                'descripcion': f"{usr_name} registró una {pqr.get_tipo_display()}: '{pqr.asunto}'",
                'fecha': pqr.fecha,
                'monto': None
            })

        actividades.sort(key=lambda x: x['fecha'], reverse=True)
        actividad_reciente = actividades[:6]

        nivel_viajero = "Director de Expediciones"
        descripcion_nivel = "Panel de control y estadísticas globales de Monagua."
        progreso_nivel = 100
        dias_como_miembro = max(1, (now - request.user.date_joined).days)

        template_name = 'admin/estadisticas_admin.html'

    else:
        # 2. Individual Statistics (Tourist)
        cliente_obj = Cliente.objects.filter(usuario=request.user).first()

        total_reservas = Reserva.objects.filter(usuario=request.user).count()
        reservas_confirmadas = Reserva.objects.filter(usuario=request.user, estado='confirmada').count()
        reservas_pendientes = Reserva.objects.filter(usuario=request.user, estado='pendiente').count()
        reservas_canceladas = Reserva.objects.filter(usuario=request.user, estado='cancelada').count()
        reservas_completadas = Reserva.objects.filter(usuario=request.user, estado='completada').count()

        total_invertido = ComprobantePago.objects.filter(usuario=request.user, estado='aprobado').aggregate(total=Sum('monto'))['total'] or 0.0
        pagos_pendientes = ComprobantePago.objects.filter(usuario=request.user, estado='pendiente').count()
        pagos_rechazados = ComprobantePago.objects.filter(usuario=request.user, estado='rechazado').count()
        total_comprobantes = ComprobantePago.objects.filter(usuario=request.user).count()

        reservas_pagadas = reservas_confirmadas + reservas_completadas
        promedio_por_reserva = float(total_invertido) / reservas_pagadas if reservas_pagadas > 0 else 0.0

        total_comentarios = Comentario.objects.filter(usuario=request.user).count()
        promedio_calificacion = Comentario.objects.filter(usuario=request.user).aggregate(promedio=Avg('valoracion'))['promedio'] or 0.0

        distribucion_calificaciones = []
        for estrellas in range(5, 0, -1):
            cant = Comentario.objects.filter(usuario=request.user, valoracion=estrellas).count()
            porcentaje = round((cant / total_comentarios * 100)) if total_comentarios > 0 else 0
            distribucion_calificaciones.append({
                'estrellas': estrellas,
                'cantidad': cant,
                'porcentaje': porcentaje
            })

        total_pqrs = PQRS.objects.filter(cliente=cliente_obj).count() if cliente_obj else 0
        pqrs_abiertas = PQRS.objects.filter(cliente=cliente_obj, estado='abierto').count() if cliente_obj else 0
        pqrs_en_gestion = PQRS.objects.filter(cliente=cliente_obj, estado='en_proceso').count() if cliente_obj else 0
        pqrs_cerradas = PQRS.objects.filter(cliente=cliente_obj, estado='cerrado').count() if cliente_obj else 0
        pqrs_sin_respuesta = PQRS.objects.filter(cliente=cliente_obj).filter(Q(respuesta=None) | Q(respuesta='')).count() if cliente_obj else 0

        destinos_qs = Reserva.objects.filter(usuario=request.user).values('paquete__nombre')\
            .annotate(total_reservas=Count('id'), ultima_visita=Max('fecha'))\
            .order_by('-total_reservas')[:5]
        
        destinos_frecuentes = []
        for item in destinos_qs:
            destinos_frecuentes.append({
                'nombre': item['paquete__nombre'],
                'total_reservas': item['total_reservas'],
                'ultima_visita': item['ultima_visita']
            })

        # Recent activity (tourist specific)
        reservas_recientes = Reserva.objects.filter(usuario=request.user).select_related('paquete').order_by('-fecha_registro')[:5]
        pagos_recientes = ComprobantePago.objects.filter(usuario=request.user).order_by('-fecha_envio')[:5]
        comentarios_recientes = Comentario.objects.filter(usuario=request.user).order_by('-fecha_creacion')[:5]
        pqrs_recientes = PQRS.objects.filter(cliente=cliente_obj).order_by('-fecha')[:5] if cliente_obj else []

        actividades = []
        for res in reservas_recientes:
            actividades.append({
                'tipo': 'reserva',
                'descripcion': f"Reservaste '{res.paquete.nombre}'",
                'fecha': res.fecha_registro,
                'monto': None
            })
        for comp in pagos_recientes:
            actividades.append({
                'tipo': 'pago',
                'descripcion': f"Enviaste comprobante ({comp.get_estado_display()})",
                'fecha': comp.fecha_envio,
                'monto': comp.monto
            })
        for comment in comentarios_recientes:
            actividades.append({
                'tipo': 'resena',
                'descripcion': f"Publicaste una reseña: '{comment.titulo}'",
                'fecha': comment.fecha_creacion,
                'monto': None
            })
        for pqr in pqrs_recientes:
            actividades.append({
                'tipo': 'pqrs',
                'descripcion': f"Registraste una {pqr.get_tipo_display()}: '{pqr.asunto}'",
                'fecha': pqr.fecha,
                'monto': None
            })

        actividades.sort(key=lambda x: x['fecha'], reverse=True)
        actividad_reciente = actividades[:6]

        # Traveler level logic
        viajes_validos = reservas_confirmadas + reservas_completadas
        if viajes_validos == 0:
            nivel_viajero = "Viajero Novel"
            descripcion_nivel = "¡Tu primer viaje te espera! Comienza a explorar Mongua y sube de nivel."
            progreso_nivel = 0
        elif viajes_validos in [1, 2]:
            nivel_viajero = "Explorador"
            descripcion_nivel = "Estás descubriendo la magia del páramo. ¡Sigue así!"
            progreso_nivel = int((viajes_validos / 3) * 100)
        elif viajes_validos in [3, 4, 5]:
            nivel_viajero = "Aventurero"
            descripcion_nivel = "Un viajero recurrente y apasionado por la naturaleza de Mongua."
            progreso_nivel = int((viajes_validos / 6) * 100)
        else:
            nivel_viajero = "Expedicionista"
            descripcion_nivel = "¡Eres un guardián experto del páramo y conoces cada rincón!"
            progreso_nivel = 100

        dias_como_miembro = max(1, (now - request.user.date_joined).days)

        template_name = 'private/estadisticas.html'

    # ── Datos compartidos para gráficas y tablas ──────────────────────────────
    MESES_ES  = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
    MESES_FULL = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio',
                  'Agosto','Septiembre','Octubre','Noviembre','Diciembre']

    anio_actual = now.year

    if is_admin:
        base_reservas = Reserva.objects.all()
        base_pagos    = ComprobantePago.objects.filter(estado='aprobado')
        base_pagos_all = ComprobantePago.objects.all()
    else:
        base_reservas = Reserva.objects.filter(usuario=request.user)
        base_pagos    = ComprobantePago.objects.filter(usuario=request.user, estado='aprobado')
        base_pagos_all = ComprobantePago.objects.filter(usuario=request.user)

    # ── Tasa de éxito ─────────────────────────────────────────────────────────
    procesadas_totales = reservas_confirmadas + reservas_canceladas + reservas_completadas
    tasa_exito = round((reservas_confirmadas + reservas_completadas) / procesadas_totales * 100) if procesadas_totales > 0 else 0

    # ── Promedio mensual de reservas ──────────────────────────────────────────
    promedio_mensual_reservas = round(total_reservas / max(1, dias_como_miembro / 30), 1)

    # ── Árboles conservados (estimado decorativo) ─────────────────────────────
    arboles_conservados = (reservas_confirmadas + reservas_completadas) * 3

    # ── Reporte mensual (año en curso) ────────────────────────────────────────
    reporte_mensual   = []
    meses_labels_list = []
    meses_datos_list  = []
    meses_inversion_list = []

    for mes in range(1, 13):
        qs_mes             = base_reservas.filter(fecha__year=anio_actual, fecha__month=mes)
        total_creadas      = qs_mes.count()
        total_confirmadas  = qs_mes.filter(estado='confirmada').count()
        total_canceladas   = qs_mes.filter(estado='cancelada').count()
        total_completadas  = qs_mes.filter(estado='completada').count()
        exitosas_mes       = total_confirmadas + total_completadas
        procesadas_mes     = total_confirmadas + total_canceladas + total_completadas
        porcentaje_exito_m = round(exitosas_mes / procesadas_mes * 100) if procesadas_mes > 0 else 0
        inv = base_pagos.filter(
            fecha_envio__year=anio_actual,
            fecha_envio__month=mes
        ).aggregate(total=Sum('monto'))['total'] or 0

        reporte_mensual.append({
            'mes_nombre':        MESES_FULL[mes - 1],
            'anio':              anio_actual,
            'total_creadas':     total_creadas,
            'total_confirmadas': total_confirmadas,
            'total_canceladas':  total_canceladas,
            'total_completadas': total_completadas,
            'porcentaje_exito':  porcentaje_exito_m,
            'inversion':         inv,
        })
        meses_labels_list.append(MESES_ES[mes - 1])
        meses_datos_list.append(total_creadas)
        meses_inversion_list.append(float(inv))

    # ── Reporte anual (todos los años con reservas) ───────────────────────────
    anios_qs           = base_reservas.values('fecha__year').annotate(total=Count('id')).order_by('fecha__year')
    reporte_anual      = []
    anios_labels_list  = []
    anios_datos_list   = []
    anios_reservas_list = []
    anios_canceladas_list = []

    for row in anios_qs:
        anio = row['fecha__year']
        if anio is None:
            continue
        qs_anio         = base_reservas.filter(fecha__year=anio)
        total_anio      = qs_anio.count()
        conf_a          = qs_anio.filter(estado='confirmada').count()
        canc_a          = qs_anio.filter(estado='cancelada').count()
        comp_a          = qs_anio.filter(estado='completada').count()
        exitosas_a      = conf_a + comp_a
        procesadas_a    = conf_a + canc_a + comp_a
        porcentaje_a    = round((exitosas_a / procesadas_a) * 100) if procesadas_a > 0 else 0
        inversion_anio  = base_pagos.filter(fecha_envio__year=anio).aggregate(
            total=Sum('monto')
        )['total'] or 0
        ticket_prom_a   = round(float(inversion_anio) / exitosas_a) if exitosas_a > 0 else 0

        reporte_anual.append({
            'anio':              anio,
            'total_reservas':    total_anio,
            'total_confirmadas': conf_a,
            'total_canceladas':  canc_a,
            'total_completadas': comp_a,
            'porcentaje_exito':  porcentaje_a,
            'ticket_promedio':   ticket_prom_a,
            'inversion':         inversion_anio,
        })
        anios_labels_list.append(str(anio))
        anios_datos_list.append(float(inversion_anio))
        anios_reservas_list.append(total_anio)
        anios_canceladas_list.append(canc_a)

    # ── Distribución por día de la semana ─────────────────────────────────────
    dias_datos_list = [0] * 7
    for r in base_reservas.filter(fecha__year=anio_actual):
        if r.fecha:
            dias_datos_list[r.fecha.weekday()] += 1

    # ── Destinos: enriquecer con inversión y generar labels/datos para chart ──
    destinos_qs_full = base_reservas.values('paquete__nombre').annotate(
        total_reservas=Count('id'),
        ultima_visita=Max('fecha'),
        inversion_total=Sum('monto_total'),
    ).order_by('-total_reservas')[:5]

    destinos_frecuentes = []
    destinos_top_labels_list = []
    destinos_top_datos_list  = []
    for item in destinos_qs_full:
        destinos_frecuentes.append({
            'nombre':          item['paquete__nombre'],
            'total_reservas':  item['total_reservas'],
            'inversion_total': item['inversion_total'] or 0,
            'ultima_visita':   item['ultima_visita'],
        })
        destinos_top_labels_list.append(item['paquete__nombre'] or '—')
        destinos_top_datos_list.append(item['total_reservas'])

    # ── Historial de pagos (para tab transacciones) ───────────────────────────
    historial_pagos = []
    for pago in base_pagos_all.select_related('reserva__paquete').order_by('-fecha_envio')[:15]:
        historial_pagos.append({
            'codigo':        f"#CP-{pago.pk}",
            'reserva_nombre': pago.reserva.paquete.nombre if pago.reserva and pago.reserva.paquete else '—',
            'metodo':         pago.banco_origen or 'Transferencia',
            'estado':         pago.estado,
            'fecha':          pago.fecha_envio,
            'monto':          pago.monto or 0,
        })

    # ── Reseñas del usuario (para tab reseñas) ────────────────────────────────
    if is_admin:
        resenas_qs = Comentario.objects.select_related('paquete').order_by('-fecha_creacion')[:15]
    else:
        resenas_qs = Comentario.objects.filter(usuario=request.user).select_related('paquete').order_by('-fecha_creacion')[:15]

    mis_resenas = []
    for r in resenas_qs:
        mis_resenas.append({
            'destino':      r.paquete.nombre if r.paquete else r.titulo,
            'calificacion': r.valoracion,
            'comentario':   r.mensaje,
            'publicada':    r.visible,
            'fecha':        r.fecha_creacion,
        })

    # ── Radar de perfil (normalizado a 100) ───────────────────────────────────
    max_reservas_r = max(total_reservas, 1)
    max_inversion_r = max(float(total_invertido), 1)
    radar_datos_list = [
        min(100, round(total_reservas / 10 * 100)),              # Reservas
        min(100, round(float(total_invertido) / 5000000 * 100)), # Inversión
        min(100, progreso_nivel),                                 # Fidelidad
        min(100, round(total_comentarios / 5 * 100)),            # Reseñas
        min(100, round(pqrs_cerradas / max(total_pqrs, 1) * 100)), # PQRS resueltas
        min(100, round(len(destinos_frecuentes) / 5 * 100)),    # Destinos
    ]

    # ── PQRS tasa resolución ──────────────────────────────────────────────────
    pqrs_tasa_resolucion = round(pqrs_cerradas / total_pqrs * 100) if total_pqrs > 0 else 0

    context = {
        # KPIs principales
        'total_reservas':              total_reservas,
        'reservas_confirmadas':        reservas_confirmadas,
        'reservas_pendientes':         reservas_pendientes,
        'reservas_canceladas':         reservas_canceladas,
        'reservas_completadas':        reservas_completadas,
        'total_invertido':             total_invertido,
        'pagos_pendientes':            pagos_pendientes,
        'pagos_rechazados':            pagos_rechazados,
        'total_comprobantes':          total_comprobantes,
        'promedio_por_reserva':        promedio_por_reserva,
        'tasa_exito':                  tasa_exito,
        'promedio_mensual_reservas':   promedio_mensual_reservas,
        'arboles_conservados':         arboles_conservados,
        # Reseñas
        'total_comentarios':           total_comentarios,
        'total_resenas':               total_comentarios,
        'promedio_calificacion':       promedio_calificacion,
        'distribucion_calificaciones': distribucion_calificaciones,
        # PQRS
        'total_pqrs':                  total_pqrs,
        'pqrs_total':                  total_pqrs,
        'pqrs_abiertas':               pqrs_abiertas,
        'pqrs_en_gestion':             pqrs_en_gestion,
        'pqrs_cerradas':               pqrs_cerradas,
        'pqrs_sin_respuesta':          pqrs_sin_respuesta,
        'pqrs_tasa_resolucion':        pqrs_tasa_resolucion,
        # Destinos y actividad
        'destinos_frecuentes':         destinos_frecuentes,
        'total_destinos':              len(destinos_frecuentes),
        'actividad_reciente':          actividad_reciente,
        # Nivel / fidelización
        'nivel_viajero':               nivel_viajero,
        'descripcion_nivel':           descripcion_nivel,
        'progreso_nivel':              progreso_nivel,
        'dias_como_miembro':           dias_como_miembro,
        # Tablas de reporte
        'reporte_mensual':             reporte_mensual,
        'reporte_anual':               reporte_anual,
        # Historial de pagos y reseñas
        'historial_pagos':             historial_pagos,
        'mis_resenas':                 mis_resenas,
        # Datos JSON para gráficas Chart.js
        'meses_labels':          json.dumps(meses_labels_list, ensure_ascii=False),
        'meses_datos':           json.dumps(meses_datos_list),
        'meses_inversion':       json.dumps(meses_inversion_list),
        'anios_labels':          json.dumps(anios_labels_list, ensure_ascii=False),
        'anios_datos':           json.dumps(anios_datos_list),
        'anios_reservas':        json.dumps(anios_reservas_list),
        'anios_canceladas':      json.dumps(anios_canceladas_list),
        'dias_datos':            json.dumps(dias_datos_list),
        'destinos_top_labels':   json.dumps(destinos_top_labels_list, ensure_ascii=False),
        'destinos_top_datos':    json.dumps(destinos_top_datos_list),
        'radar_datos':           json.dumps(radar_datos_list),
    }

    return render(request, template_name, context)



@login_required
def dashboard_turista(request):
    if request.user.is_staff:
        return redirect('dashboard')

    from reservas.models import Reserva
    from pagos.models import ComprobantePago
    from comunidad.models import PQRS
    from .models import Comentario, Cliente
    from django.db.models import Sum

    total_reservas = Reserva.objects.filter(usuario=request.user).count()
    reservas_confirmadas = Reserva.objects.filter(usuario=request.user, estado='confirmada').count()
    reservas_pendientes  = Reserva.objects.filter(usuario=request.user, estado='pendiente').count()
    reservas_canceladas  = Reserva.objects.filter(usuario=request.user, estado='cancelada').count()

    tasa_confirmacion = 0
    if total_reservas > 0:
        tasa_confirmacion = round((reservas_confirmadas / total_reservas) * 100)

    total_invertido = ComprobantePago.objects.filter(
        usuario=request.user, estado='aprobado'
    ).aggregate(total=Sum('monto'))['total'] or 0.0

    total_comentarios = Comentario.objects.filter(usuario=request.user).count()

    total_pqrs = 0
    try:
        cliente_obj = Cliente.objects.get(usuario=request.user)
        total_pqrs = PQRS.objects.filter(cliente=cliente_obj).count()
    except Cliente.DoesNotExist:
        pass

    ultimas_reservas = Reserva.objects.filter(
        usuario=request.user
    ).select_related('paquete').order_by('-id')[:5]

    context = {
        'total_reservas':       total_reservas,
        'reservas_confirmadas': reservas_confirmadas,
        'reservas_pendientes':  reservas_pendientes,
        'reservas_canceladas':  reservas_canceladas,
        'tasa_confirmacion':    tasa_confirmacion,
        'total_invertido':      total_invertido,
        'total_comentarios':    total_comentarios,
        'total_pqrs':           total_pqrs,
        'ultimas_reservas':     ultimas_reservas,
    }
    return render(request, 'private/dashboard_turista.html', context)


@login_required
def mis_rechazos(request):
    if request.user.is_staff:
        return redirect('dashboard')

    from pagos.models import ComprobantePago
    from reservas.models import Cancelacion

    # Fetch rejected payments for the user
    pagos_rechazados = ComprobantePago.objects.filter(
        usuario=request.user,
        estado='rechazado'
    ).select_related('reserva__paquete').order_by('-fecha_revision')

    # Fetch rejected cancellations for the user
    cancelaciones_rechazadas = Cancelacion.objects.filter(
        reserva__usuario=request.user,
        estado='rechazada'
    ).select_related('reserva__paquete').order_by('-id')

    context = {
        'pagos_rechazados': pagos_rechazados,
        'cancelaciones_rechazadas': cancelaciones_rechazadas,
        'total_pagos_rechazados': pagos_rechazados.count(),
        'total_cancelaciones_rechazadas': cancelaciones_rechazadas.count(),
    }
    return render(request, 'private/rechazos.html', context)