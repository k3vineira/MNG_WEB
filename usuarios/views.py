from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Avg
from .models import Usuario, Cliente, GuiaTuristico
from comunidad.models import Comentario
from .forms import PerfilUsuarioForm

# 1. VISTAS PÚBLICAS / ESTÁTICAS

def terminos_view(request):
    """Renderiza la plantilla de términos y condiciones."""
    return render(request, 'public/terminos.html', {
        'titulo': 'Términos y Condiciones — Monagua'
    })


def nosotros_view(request):
    """Renderiza la plantilla de información corporativa."""
    return render(request, 'public/nosotros.html', {
        'titulo': 'Sobre Nosotros — Monagua'
    })


# 3. PANELES DE CONTROL (DASHBOARDS)

@login_required
def index_turista(request):
    """Renderiza el panel rápido exclusivo para clientes/turistas."""
    if request.user.is_staff:
        return redirect('dashboard')

    from reservas.models import Reserva
    from pagos.models import ComprobantePago
    from comunidad.models import Comentario, PQRS
    from django.db.models import Sum

    # Calculate stats for the dashboard
    total_invertido = ComprobantePago.objects.filter(usuario=request.user, estado='aprobado').aggregate(Sum('monto'))['monto__sum'] or 0
    total_reservas = Reserva.objects.filter(usuario=request.user).count()
    total_comentarios = Comentario.objects.filter(usuario=request.user).count()
    total_pqrs = PQRS.objects.filter(cliente__usuario=request.user).count()

    reservas_confirmadas = Reserva.objects.filter(usuario=request.user, estado='confirmada').count()
    reservas_pendientes = Reserva.objects.filter(usuario=request.user, estado='pendiente').count()
    reservas_canceladas = Reserva.objects.filter(usuario=request.user, estado='cancelada').count()

    tasa_confirmacion = int(reservas_confirmadas / total_reservas * 100) if total_reservas > 0 else 0
    ultimas_reservas = Reserva.objects.filter(usuario=request.user).select_related('paquete').order_by('-fecha_registro')[:5]

    return render(request, 'private/dashboard_turista.html', {
        'titulo': 'Bienvenido a Monagua',
        'total_invertido': total_invertido,
        'total_reservas': total_reservas,
        'total_comentarios': total_comentarios,
        'total_pqrs': total_pqrs,
        'reservas_confirmadas': reservas_confirmadas,
        'reservas_pendientes': reservas_pendientes,
        'reservas_canceladas': reservas_canceladas,
        'tasa_confirmacion': tasa_confirmacion,
        'ultimas_reservas': ultimas_reservas,
    })


@user_passes_test(lambda u: u.is_staff)
def dashboard_admin(request):
    """Renderiza el tablero de control principal del administrador."""
    import datetime
    from django.utils import timezone
    from django.db.models import Sum, Count, Avg
    from reservas.models import Reserva, Cancelacion
    from pagos.models import ComprobantePago
    from catalogo.models import Paquete
    from comunidad.models import Comentario

    hoy = timezone.now().date()
    total_usuarios = Usuario.objects.count()
    total_reservas = Reserva.objects.count()

    total_ventas = ComprobantePago.objects.filter(estado='aprobado').aggregate(Sum('monto'))['monto__sum'] or 0
    total_tours = Paquete.objects.filter(estado=True).count()
    total_pagos_rechazados = ComprobantePago.objects.filter(estado='rechazado').count()
    
    from promociones.models import Promocion, Banner
    total_promociones = Promocion.objects.count() + Banner.objects.count()

    current_year = timezone.now().year
    ingresos_mensuales = [0] * 12
    for p in ComprobantePago.objects.filter(estado='aprobado', fecha_envio__year=current_year):
        m = p.fecha_envio.month - 1
        ingresos_mensuales[m] += float(p.monto or 0)

    reservas_confirmadas = Reserva.objects.filter(estado='confirmada').count()
    reservas_pendientes = Reserva.objects.filter(estado='pendiente').count()
    reservas_canceladas = Reserva.objects.filter(estado='cancelada').count()

    # Reservas de la semana actual (Lunes a Domingo)
    start_of_week = hoy - datetime.timedelta(days=hoy.weekday())
    end_of_week = start_of_week + datetime.timedelta(days=6)
    reservas_semana = [0] * 7
    for r in Reserva.objects.filter(fecha__range=[start_of_week, end_of_week]):
        reservas_semana[r.fecha.weekday()] += 1

    tasa_confirmacion = int(reservas_confirmadas / total_reservas * 100) if total_reservas > 0 else 0

    val_avg = Comentario.objects.aggregate(Avg('valoracion'))['valoracion__avg']
    valoracion_promedio = round(val_avg, 1) if val_avg is not None else 0.0

    ingreso_por_reserva = total_ventas / total_reservas if total_reservas > 0 else 0

    cancelaciones_hoy = Cancelacion.objects.filter(reserva__fecha=hoy).count()
    cancelaciones_rechazadas = Cancelacion.objects.filter(estado='rechazada').count()
    cancelaciones_pendientes = Cancelacion.objects.filter(estado='revision').count()

    packages = Paquete.objects.filter(estado=True).annotate(
        numero_reservas=Count('reserva')
    ).order_by('-numero_reservas')[:5]
    tours_populares = [{
        'nombre': p.nombre,
        'precio': p.precio_minimo,
        'numero_reservas': p.numero_reservas,
    } for p in packages]
    max_reservas = max([t['numero_reservas'] for t in tours_populares], default=1)
    if max_reservas == 0:
        max_reservas = 1

    # Actividad reciente
    from django.utils.timesince import timesince
    actividad_reciente = []
    for r in Reserva.objects.select_related('usuario', 'paquete').order_by('-fecha_registro')[:5]:
        nombre_usr = r.usuario.get_full_name() or r.usuario.username
        actividad_reciente.append({
            'texto': f"Nueva reserva de {nombre_usr} para {r.paquete.nombre}",
            'tiempo_dt': r.fecha_registro,
        })
    for p in ComprobantePago.objects.select_related('usuario').order_by('-fecha_envio')[:5]:
        nombre_usr = p.usuario.get_full_name() or p.usuario.username
        actividad_reciente.append({
            'texto': f"Pago de COP ${p.monto or 0:,.0f} enviado por {nombre_usr} ({p.get_estado_display()})",
            'tiempo_dt': p.fecha_envio,
        })
    actividad_reciente.sort(key=lambda x: x['tiempo_dt'], reverse=True)
    actividad_reciente = actividad_reciente[:5]
    for item in actividad_reciente:
        try:
            item['tiempo'] = f"Hace {timesince(item['tiempo_dt'])}"
        except Exception:
            item['tiempo'] = item['tiempo_dt'].strftime("%d/%m/%Y %H:%M")

    return render(request, 'admin/index-admin.html', {
        'titulo': 'Tablero de Rendimiento — Administración',
        'total_usuarios': total_usuarios,
        'total_reservas': total_reservas,
        'total_ventas': total_ventas,
        'total_tours': total_tours,
        'total_pagos_rechazados': total_pagos_rechazados,
        'total_promociones': total_promociones,
        'ingresos_mensuales': ingresos_mensuales,
        'reservas_confirmadas': reservas_confirmadas,
        'reservas_pendientes': reservas_pendientes,
        'reservas_canceladas': reservas_canceladas,
        'reservas_semana': reservas_semana,
        'tasa_confirmacion': tasa_confirmacion,
        'valoracion_promedio': valoracion_promedio,
        'ingreso_por_reserva': ingreso_por_reserva,
        'cancelaciones_hoy': cancelaciones_hoy,
        'cancelaciones_rechazadas': cancelaciones_rechazadas,
        'cancelaciones_pendientes': cancelaciones_pendientes,
        'tours_populares': tours_populares,
        'max_reservas': max_reservas,
        'actividad_reciente': actividad_reciente,
    })

# 4. GESTIÓN DE PERFILES Y USUARIOS


@login_required
def perfil_detalles(request):
    """Renderiza dinámicamente el perfil correspondiente según el rol (Admin o Turista)."""
    if request.method == 'POST':
        if 'imagen_perfil' in request.FILES and not request.POST.get('editar_perfil'):
            request.user.imagen_perfil = request.FILES['imagen_perfil']
            request.user.save()
            messages.success(
                request, 'Foto de perfil actualizada correctamente.')
            return redirect('perfil_detalles')

        form = PerfilUsuarioForm(
            request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil actualizado correctamente.')
            return redirect('perfil_detalles')
    else:
        form = PerfilUsuarioForm(instance=request.user)

    template_name = 'admin/perfil_admin.html' if request.user.is_staff else 'private/perfil_turista.html'

    return render(request, template_name, {
        'titulo': 'Mi Perfil — Monagua',
        'form': form
    })


@user_passes_test(lambda u: u.is_staff)
def gestion_usuarios(request, id=None):
    """Renderiza el panel de control integral para la gestión de todos los Usuarios."""
    # Filtro por rol (viene del query string ?filtro=ADMIN|GUIA|CLIENTE)
    filtro = request.GET.get('filtro', '')
    usuarios = Usuario.objects.all().select_related('cliente', 'guia')
    if filtro in [r.value for r in Usuario.Roles]:
        usuarios = usuarios.filter(rol=filtro)

    # Conteos rápidos para los badges del encabezado
    total_admins = Usuario.objects.filter(rol=Usuario.Roles.ADMIN).count()
    total_guias = Usuario.objects.filter(rol=Usuario.Roles.GUIA).count()
    total_clientes = Usuario.objects.filter(rol=Usuario.Roles.CLIENTE).count()

    return render(request, 'admin/gestion_usuarios.html', {
        'titulo': 'Gestión de Usuarios — Monagua',
        'usuarios': usuarios,
        'filtro_actual': filtro,
        'total_admins': total_admins,
        'total_guias': total_guias,
        'total_clientes': total_clientes,
    })


@user_passes_test(lambda u: u.is_staff)
def usuarios_guardar(request):
    """
    Acción unificada para crear o actualizar un Usuario de cualquier rol.
    Si el POST incluye 'id', edita; si no, crea uno nuevo.
    Según el rol seleccionado, crea/actualiza el perfil Cliente o GuiaTuristico.
    """
    if request.method != 'POST':
        return redirect('gestion_usuarios')

    user_id = request.POST.get('id')
    rol = request.POST.get('rol', Usuario.Roles.CLIENTE)

    if user_id:
        # --- MODO EDICIÓN ---
        user = get_object_or_404(Usuario, id=user_id)
        email = request.POST.get('email', '').strip()
        if not email:
            messages.error(request, 'El email es obligatorio.')
            return redirect('gestion_usuarios')
        if Usuario.objects.filter(email__iexact=email).exclude(id=user.id).exists():
            messages.error(request, f'El correo electrónico «{email}» ya está registrado en otra cuenta.')
            return redirect('gestion_usuarios')

        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = email
        user.tipo_documento = request.POST.get(
            'tipo_documento', user.tipo_documento)
        user.numero_documento = request.POST.get(
            'numero_documento', user.numero_documento)
        user.telefono = request.POST.get('telefono', user.telefono)
        user.residencia = request.POST.get('residencia', user.residencia)
        user.rol = rol
        if rol == Usuario.Roles.ADMIN:
            user.is_staff = True
        if 'imagen_perfil' in request.FILES:
            user.imagen_perfil = request.FILES['imagen_perfil']
        password = request.POST.get('password', '').strip()
        if password:
            user.set_password(password)
        user.save()
    else:
        # --- MODO CREACIÓN ---
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        if not username or not email:
            messages.error(
                request, 'El nombre de usuario y el email son obligatorios.')
            return redirect('gestion_usuarios')
        if Usuario.objects.filter(username=username).exists():
            messages.error(request, f'El usuario «{username}» ya existe.')
            return redirect('gestion_usuarios')
        if Usuario.objects.filter(email__iexact=email).exists():
            messages.error(request, f'El correo electrónico «{email}» ya está registrado en otra cuenta.')
            return redirect('gestion_usuarios')

        user = Usuario(
            username=username,
            email=email,
            first_name=request.POST.get('first_name', ''),
            last_name=request.POST.get('last_name', ''),
            tipo_documento=request.POST.get('tipo_documento', ''),
            numero_documento=request.POST.get('numero_documento', ''),
            telefono=request.POST.get('telefono', ''),
            residencia=request.POST.get('residencia', ''),
            rol=rol,
            is_staff=(rol == Usuario.Roles.ADMIN),
        )
        password = request.POST.get('password', '').strip()
        user.set_password(password if password else request.POST.get(
            'numero_documento', username))
        if 'imagen_perfil' in request.FILES:
            user.imagen_perfil = request.FILES['imagen_perfil']
        user.save()

    # --- Crear / actualizar perfil específico según rol ---
    if rol == Usuario.Roles.CLIENTE:
        perfil, _ = Cliente.objects.get_or_create(usuario=user)
        perfil.pais = request.POST.get('pais', perfil.pais)
        perfil.ciudad = request.POST.get('ciudad', perfil.ciudad)
        perfil.save()
    elif rol == Usuario.Roles.GUIA:
        perfil, _ = GuiaTuristico.objects.get_or_create(usuario=user)
        perfil.licencia_turismo = request.POST.get(
            'licencia_turismo', perfil.licencia_turismo)
        experiencia = request.POST.get('experiencia_anos', '0')
        perfil.experiencia_anos = int(
            experiencia) if experiencia.isdigit() else 0
        perfil.biografia = request.POST.get('biografia', perfil.biografia)
        perfil.save()

    accion = 'actualizado' if user_id else 'registrado'
    messages.success(
        request, f'Usuario «{user.get_full_name()}» {accion} correctamente.')
    return redirect('gestion_usuarios')


@user_passes_test(lambda u: u.is_staff)
def usuarios_toggle_estado(request, user_id):
    """Acción de backend para alternar el estado activo/inactivo de un usuario (Redirecciona)."""
    if request.method == 'POST':
        user = get_object_or_404(Usuario, id=user_id)
        user.is_active = not user.is_active
        user.save()
        estado = 'activado' if user.is_active else 'inactivado'
        messages.info(request, f'Usuario «{user.get_full_name()}» {estado}.')
    return redirect('gestion_usuarios')


@user_passes_test(lambda u: u.is_staff)
def gestion_guias(request, id=None):
    """Renderiza el panel de control y auditoría para la gestión de Guías."""
    guias = Usuario.objects.filter(
        rol=Usuario.Roles.GUIA).select_related('guia')
    guias_activos = guias.filter(is_active=True).count()
    guia_seleccionado = None
    if id:
        guia_seleccionado = get_object_or_404(
            Usuario, id=id, rol=Usuario.Roles.GUIA)
    return render(request, 'admin/gestion_guias.html', {
        'titulo': 'Gestión de Guías — Monagua',
        'guias': guias,
        'guias_activos': guias_activos,
        'guia_seleccionado': guia_seleccionado,
        'id': id
    })


@user_passes_test(lambda u: u.is_staff)
def asignar_rol_guia(request, user_id):
    """Acción de backend para alternar el rol de guía (Redirecciona)."""
    if request.method == 'POST':
        user = get_object_or_404(Usuario, id=user_id)
        if user.rol != Usuario.Roles.GUIA:
            user.rol = Usuario.Roles.GUIA
            user.save()
            GuiaTuristico.objects.get_or_create(usuario=user)
            messages.success(
                request, f'Rol de guía asignado a {user.username}')
        else:
            user.rol = Usuario.Roles.CLIENTE
            user.save()
            messages.info(request, f'Rol de guía removido de {user.username}')
    return redirect('gestion_guias')


@user_passes_test(lambda u: u.is_staff)
def guias_guardar(request):
    """
    Acción de backend unificada para crear o actualizar un Guía Turístico.
    Si el POST incluye 'id', edita el usuario existente.
    Si no, crea un nuevo Usuario con rol GUIA y su perfil GuiaTuristico.
    """
    if request.method != 'POST':
        return redirect('gestion_guias')

    guia_id = request.POST.get('id')

    if guia_id:
        # --- MODO EDICIÓN ---
        user = get_object_or_404(Usuario, id=guia_id, rol=Usuario.Roles.GUIA)
        email = request.POST.get('email', '').strip()
        if not email:
            messages.error(request, 'El email es obligatorio.')
            return redirect('gestion_guias')
        if Usuario.objects.filter(email__iexact=email).exclude(id=user.id).exists():
            messages.error(request, f'El correo electrónico «{email}» ya está registrado en otra cuenta.')
            return redirect('gestion_guias')

        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = email
        user.tipo_documento = request.POST.get(
            'tipo_documento', user.tipo_documento)
        user.numero_documento = request.POST.get(
            'numero_documento', user.numero_documento)
        user.telefono = request.POST.get('telefono', user.telefono)
        user.residencia = request.POST.get('residencia', user.residencia)
        if 'imagen_perfil' in request.FILES:
            user.imagen_perfil = request.FILES['imagen_perfil']
        user.save()

        perfil, _ = GuiaTuristico.objects.get_or_create(usuario=user)
        perfil.licencia_turismo = request.POST.get(
            'licencia_turismo', perfil.licencia_turismo)
        experiencia = request.POST.get('experiencia_anos')
        if experiencia and experiencia.isdigit():
            perfil.experiencia_anos = int(experiencia)
        perfil.biografia = request.POST.get('biografia', perfil.biografia)
        perfil.save()
        messages.success(
            request, f'Guía «{user.get_full_name()}» actualizado correctamente.')

    else:
        # --- MODO CREACIÓN ---
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()

        if not username or not email:
            messages.error(
                request, 'El nombre de usuario y el email son obligatorios.')
            return redirect('gestion_guias')

        if Usuario.objects.filter(username=username).exists():
            messages.error(
                request, f'El nombre de usuario «{username}» ya está en uso.')
            return redirect('gestion_guias')

        if Usuario.objects.filter(email__iexact=email).exists():
            messages.error(
                request, f'El correo electrónico «{email}» ya está en uso por otra cuenta.')
            return redirect('gestion_guias')

        # Crear el usuario base con rol GUIA
        user = Usuario(
            username=username,
            email=email,
            first_name=request.POST.get('first_name', ''),
            last_name=request.POST.get('last_name', ''),
            tipo_documento=request.POST.get('tipo_documento', ''),
            numero_documento=request.POST.get('numero_documento', ''),
            telefono=request.POST.get('telefono', ''),
            residencia=request.POST.get('residencia', ''),
            rol=Usuario.Roles.GUIA,
        )
        # Contraseña temporal = número de documento (el guía la cambiará después)
        password = request.POST.get('numero_documento', username)
        user.set_password(password)
        if 'imagen_perfil' in request.FILES:
            user.imagen_perfil = request.FILES['imagen_perfil']
        user.save()

        # Crear el perfil profesional del guía
        experiencia = request.POST.get('experiencia_anos', '0')
        GuiaTuristico.objects.create(
            usuario=user,
            licencia_turismo=request.POST.get('licencia_turismo', ''),
            experiencia_anos=int(experiencia) if experiencia.isdigit() else 0,
            biografia=request.POST.get('biografia', ''),
        )
        messages.success(
            request, f'Guía «{user.get_full_name()}» registrado exitosamente.')

    return redirect('gestion_guias')




def get_estadisticas_context(user, is_admin=False):
    import datetime
    from django.db.models import Sum, Count, Avg, Max
    from django.utils import timezone
    from reservas.models import Reserva
    from pagos.models import ComprobantePago
    from comunidad.models import Comentario, PQRS

    # Base querysets
    if is_admin:
        reservas = Reserva.objects.all()
        pagos = ComprobantePago.objects.all()
        comentarios = Comentario.objects.all()
        pqrs_qs = PQRS.objects.all()
    else:
        reservas = Reserva.objects.filter(usuario=user)
        pagos = ComprobantePago.objects.filter(usuario=user)
        comentarios = Comentario.objects.filter(usuario=user)
        pqrs_qs = PQRS.objects.filter(cliente__usuario=user)

    # Basic KPI metrics
    total_invertido = pagos.filter(estado='aprobado').aggregate(Sum('monto'))['monto__sum'] or 0
    total_reservas = reservas.count()
    promedio_por_reserva = total_invertido / total_reservas if total_reservas > 0 else 0
    destinos_total = reservas.filter(estado='confirmada').values('paquete').distinct().count()
    
    reservas_confirmadas = reservas.filter(estado='confirmada').count()
    reservas_pendientes = reservas.filter(estado='pendiente').count()
    reservas_canceladas = reservas.filter(estado='cancelada').count()
    reservas_completadas = 0
    
    # Calculate completed vs confirmed based on date
    today = datetime.date.today()
    reservas_completadas = reservas.filter(estado='confirmada', fecha__lt=today).count()
    reservas_confirmadas = reservas.filter(estado='confirmada', fecha__gte=today).count()

    tasa_exito = int((reservas_confirmadas + reservas_completadas) / total_reservas * 100) if total_reservas > 0 else 0
    
    pqrs_abiertas = pqrs_qs.filter(estado='abierto').count()
    pqrs_en_gestion = pqrs_qs.filter(estado='en_proceso').count()
    pqrs_cerradas = pqrs_qs.filter(estado='cerrado').count()
    pqrs_total = pqrs_abiertas + pqrs_en_gestion + pqrs_cerradas
    pqrs_tasa_resolucion = int(pqrs_cerradas / pqrs_total * 100) if pqrs_total > 0 else 0
    
    total_resenas = comentarios.count()
    dias_como_miembro = max(0, (timezone.now() - user.date_joined).days)

    # Actividad reciente
    actividad_reciente = []
    # Obtener reservas recientes
    for r in reservas.select_related('usuario', 'paquete').order_by('-fecha_registro')[:5]:
        nombre_usr = r.usuario.get_full_name() or r.usuario.username
        if is_admin:
            desc = f"Nueva reserva de {nombre_usr} para {r.paquete.nombre}"
        else:
            desc = f"Reservaste {r.paquete.nombre}"
        actividad_reciente.append({
            'descripcion': desc,
            'fecha': r.fecha_registro,
        })
    # Obtener comprobantes de pago recientes
    for p in pagos.select_related('usuario', 'reserva', 'reserva__paquete').order_by('-fecha_envio')[:5]:
        nombre_usr = p.usuario.get_full_name() or p.usuario.username
        monto_formatted = f"COP ${p.monto or 0:,.0f}"
        if is_admin:
            desc = f"Pago de {monto_formatted} enviado por {nombre_usr} ({p.get_estado_display()})"
        else:
            desc = f"Pago de {monto_formatted} enviado ({p.get_estado_display()})"
        actividad_reciente.append({
            'descripcion': desc,
            'fecha': p.fecha_envio,
        })
    # Ordenar por fecha decreciente
    actividad_reciente.sort(key=lambda x: x['fecha'], reverse=True)
    actividad_reciente = actividad_reciente[:6]
    
    # Nivel de viajero
    if total_resenas >= 10:
        nivel_viajero = 'Expedicionista'
        progreso_nivel = 100
    elif total_resenas >= 5:
        nivel_viajero = 'Aventurero'
        progreso_nivel = int((total_resenas - 5) / 5 * 100)
    elif total_resenas >= 1:
        nivel_viajero = 'Explorador'
        progreso_nivel = int((total_resenas - 1) / 4 * 100)
    else:
        nivel_viajero = 'Viajero Novel'
        progreso_nivel = 0

    # Monthly data for current year
    current_year = timezone.now().year
    meses_nombres = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    meses_labels = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    meses_datos = [0] * 12
    meses_inversion = [0] * 12
    
    # Group reservations and payments by month
    for r in reservas.filter(fecha__year=current_year):
        m = r.fecha.month - 1
        meses_datos[m] += 1
        
    for p in pagos.filter(estado='aprobado', fecha_envio__year=current_year):
        m = p.fecha_envio.month - 1
        meses_inversion[m] += float(p.monto or 0)
        
    reporte_mensual = []
    for m in range(12):
        if meses_datos[m] > 0 or meses_inversion[m] > 0:
            mes_res = reservas.filter(fecha__year=current_year, fecha__month=m+1)
            total_creadas = mes_res.count()
            total_conf = mes_res.filter(estado='confirmada').count()
            total_canc = mes_res.filter(estado='cancelada').count()
            total_comp = mes_res.filter(estado='confirmada', fecha__lt=today).count()
            porcentaje_exito = int(total_conf / total_creadas * 100) if total_creadas > 0 else 0
            
            reporte_mensual.append({
                'mes_nombre': meses_nombres[m],
                'anio': current_year,
                'total_creadas': total_creadas,
                'total_confirmadas': total_conf,
                'total_canceladas': total_canc,
                'total_completadas': total_comp,
                'porcentaje_exito': porcentaje_exito,
                'inversion': meses_inversion[m]
            })

    # Annual data (last 5 years)
    reporte_anual = []
    anios_labels = []
    anios_datos = []
    anios_reservas = []
    anios_canceladas = []
    
    start_year = current_year - 4
    for y in range(start_year, current_year + 1):
        y_reservas = reservas.filter(fecha__year=y)
        y_pagos = pagos.filter(estado='aprobado', fecha_envio__year=y)
        
        y_total_res = y_reservas.count()
        y_total_conf = y_reservas.filter(estado='confirmada').count()
        y_total_canc = y_reservas.filter(estado='cancelada').count()
        y_total_comp = y_reservas.filter(estado='confirmada', fecha__lt=today).count()
        y_inversion = float(y_pagos.aggregate(Sum('monto'))['monto__sum'] or 0)
        y_ticket = y_inversion / y_total_res if y_total_res > 0 else 0
        y_porcentaje_exito = int(y_total_conf / y_total_res * 100) if y_total_res > 0 else 0
        
        anios_labels.append(str(y))
        anios_datos.append(y_inversion)
        anios_reservas.append(y_total_res)
        anios_canceladas.append(y_total_canc)
        
        if y_total_res > 0 or y_inversion > 0:
            reporte_anual.append({
                'anio': y,
                'total_reservas': y_total_res,
                'total_confirmadas': y_total_conf,
                'total_canceladas': y_total_canc,
                'total_completadas': y_total_comp,
                'ticket_promedio': y_ticket,
                'porcentaje_exito': y_porcentaje_exito,
                'inversion': y_inversion
            })

    # Days of the week preference
    dias_datos = [0] * 7
    for r in reservas:
        dias_datos[r.fecha.weekday()] += 1

    # Top destinations
    destinos_top_labels = []
    destinos_top_datos = []
    destinos_frecuentes = []
    
    top_packages = reservas.values('paquete', 'paquete__nombre').annotate(
        total_res=Count('id'),
        inversion=Sum('monto_total'),
        latest_date=Max('fecha')
    ).order_by('-total_res')[:5]
    
    for tp in top_packages:
        destinos_top_labels.append(tp['paquete__nombre'] or "Desconocido")
        destinos_top_datos.append(tp['total_res'])
        destinos_frecuentes.append({
            'nombre': tp['paquete__nombre'] or "Desconocido",
            'total_reservas': tp['total_res'],
            'inversion_total': tp['inversion'] or 0,
            'ultima_visita': tp['latest_date']
        })

    # Payment history
    historial_pagos = []
    for p in pagos.select_related('reserva', 'reserva__paquete').order_by('-fecha_envio')[:10]:
        historial_pagos.append({
            'codigo': f"#{p.pk}" if p.pk else "#—",
            'reserva_nombre': p.reserva.paquete.nombre if (p.reserva and p.reserva.paquete) else "Reserva Múltiple",
            'metodo': p.banco_origen,
            'estado': p.estado,
            'fecha': p.fecha_envio,
            'monto': p.monto or 0
        })

    # Reviews
    mis_resenas = []
    for c in comentarios.select_related('paquete').order_by('-fecha_creacion')[:10]:
        mis_resenas.append({
            'destino': c.paquete.nombre if c.paquete else "General",
            'calificacion': c.valoracion,
            'comentario': c.mensaje,
            'publicada': c.visible,
            'fecha': c.fecha_creacion
        })

    # Radar profile data (0-100 scale)
    radar_datos = [
        min(total_reservas * 10, 100),
        min(int(total_invertido / 500000), 100),
        min(dias_como_miembro // 30 * 5, 100),
        min(total_resenas * 15, 100),
        100 if pqrs_total == 0 else min(int(pqrs_cerradas / pqrs_total * 100), 100),
        min(destinos_total * 20, 100)
    ]
    
    # Environmental impact
    arboles_conservados = max(1, total_reservas * 2)

    return {
        'total_invertido': total_invertido,
        'total_reservas': total_reservas,
        'promedio_por_reserva': promedio_por_reserva,
        'destinos_total': destinos_total,
        'reservas_confirmadas': reservas_confirmadas,
        'reservas_pendientes': reservas_pendientes,
        'reservas_canceladas': reservas_canceladas,
        'reservas_completadas': reservas_completadas,
        'tasa_exito': tasa_exito,
        'pqrs_abiertas': pqrs_abiertas,
        'pqrs_en_gestion': pqrs_en_gestion,
        'pqrs_cerradas': pqrs_cerradas,
        'pqrs_total': pqrs_total,
        'pqrs_tasa_resolucion': pqrs_tasa_resolucion,
        'total_resenas': total_resenas,
        'dias_como_miembro': dias_como_miembro,
        'nivel_viajero': nivel_viajero,
        'progreso_nivel': progreso_nivel,
        'meses_labels': meses_labels,
        'meses_datos': meses_datos,
        'meses_inversion': meses_inversion,
        'anios_labels': anios_labels,
        'anios_datos': anios_datos,
        'anios_reservas': anios_reservas,
        'anios_canceladas': anios_canceladas,
        'dias_datos': dias_datos,
        'destinos_top_labels': destinos_top_labels,
        'destinos_top_datos': destinos_top_datos,
        'destinos_frecuentes': destinos_frecuentes,
        'historial_pagos': historial_pagos,
        'mis_resenas': mis_resenas,
        'radar_datos': radar_datos,
        'arboles_conservados': arboles_conservados,
        'reporte_mensual': reporte_mensual,
        'reporte_anual': reporte_anual,
        'actividad_reciente': actividad_reciente,
    }


@user_passes_test(lambda u: u.is_staff)
def estadisticas_admin(request):
    """
    Renderiza el panel de control global (Dashboard) para el Administrador.
    Calcula consolidados de reservas, auditoría de pagos, distribución de
    calificaciones y el feed de actividad reciente del sistema.
    """
    context = get_estadisticas_context(request.user, is_admin=True)
    context.update({
        'titulo': 'Métricas Globales — Panel de Administración',
        'nivel_viajero': 'Director de Expediciones',
        'admin_mode': True,
        'analitica_titulo': 'Consolidado General de Negocio',
    })
    return render(request, 'admin/estadisticas_admin.html', context)


@login_required
def estadisticas_turista(request):
    """
    Renderiza el historial métrico personalizado del Turista.
    Muestra la inversión total del usuario, el estado de sus reservas, sus PQRS
    y calcula dinámicamente su nivel de viajero según sus experiencias completadas.
    """
    context = get_estadisticas_context(request.user, is_admin=False)
    context.update({
        'titulo': 'Mis Estadísticas de Viaje — Monagua',
        'admin_mode': False,
        'analitica_titulo': 'Mis Estadísticas de Viaje',
    })
    return render(request, 'private/estadisticas.html', context)
