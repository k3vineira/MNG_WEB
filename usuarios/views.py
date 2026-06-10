from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.contrib import messages
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from .models import Usuario, Cliente, GuiaTuristico, Comentario
from .forms import RegistroForm, PerfilUsuarioForm

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

# 2. VISTAS DE AUTENTICACIÓN

def registro_view(request):
    """Renderiza y gestiona la plantilla de registro de usuarios."""
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.rol = Usuario.Roles.CLIENTE
            user.save()
            Cliente.objects.create(usuario=user)
            login(request, user)
            messages.success(request, 'Registro exitoso. ¡Bienvenido a Monagua!')
            return redirect('inicio')
        else:
            messages.error(request, 'Error en el registro. Verifique los datos.')
    else:
        form = RegistroForm()

    return render(request, 'authentication/registro.html', {
        'titulo': 'Crear Cuenta en Monagua',
        'form': form
    })

class UsuarioLoginView(LoginView):
    """Vista de inicio de sesión basada en clases para mayor robustez."""
    template_name = 'authentication/login.html'
    redirect_authenticated_user = True
    extra_context = {'titulo': 'Iniciar Sesión — Monagua'}

    def form_valid(self, form):
        """Añade un mensaje de éxito al iniciar sesión correctamente."""
        user = form.get_user()
        messages.success(self.request, f'¡Bienvenido nuevamente, {user.first_name or user.username}!')
        return super().form_valid(form)

    def get_success_url(self):
        # 1. Si existe un parámetro '?next=', respetarlo (ej: venía de reservar)
        next_url = self.request.GET.get('next') or self.request.POST.get('next')
        if next_url:
            return next_url
        
        # 2. Si no, redirigir según el rol del usuario
        if self.request.user.is_staff:
            return reverse_lazy('dashboard')
        return reverse_lazy('index_turista')

class UsuarioLogoutView(LogoutView):
    """Gestiona el cierre de sesión y redirige al inicio."""
    next_page = reverse_lazy('inicio')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            messages.info(request, "Has cerrado sesión correctamente. ¡Vuelve pronto!")
        return super().dispatch(request, *args, **kwargs)


# 3. PANELES DE CONTROL (DASHBOARDS)

@login_required
def index_turista(request):
    """Renderiza el panel rápido exclusivo para clientes/turistas."""
    if request.user.is_staff:
        return redirect('dashboard')
        
    return render(request, 'partials/panel_rapido.html', {
        'titulo': 'Bienvenido a Monagua'
    })

@user_passes_test(lambda u: u.is_staff)
def dashboard_admin(request):
    """Renderiza el tablero de control principal del administrador."""
    try:
        from reservas.models import Reserva
        total_reservas = Reserva.objects.count()
    except ImportError:
        total_reservas = 0

    total_usuarios = Usuario.objects.count()
    
    return render(request, 'admin/index-admin.html', {
        'titulo': 'Tablero de Rendimiento — Administración',
        'total_usuarios': total_usuarios,
        'total_reservas': total_reservas
    })

# 4. GESTIÓN DE PERFILES Y USUARIOS

@login_required
def perfil_detalles(request):
    """Renderiza dinámicamente el perfil correspondiente según el rol (Admin o Turista)."""
    if request.method == 'POST':
        if 'imagen_perfil' in request.FILES and not request.POST.get('editar_perfil'):
            request.user.imagen_perfil = request.FILES['imagen_perfil']
            request.user.save()
            messages.success(request, 'Foto de perfil actualizada correctamente.')
            return redirect('perfil_detalles')
            
        form = PerfilUsuarioForm(request.POST, request.FILES, instance=request.user)
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
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.tipo_documento = request.POST.get('tipo_documento', user.tipo_documento)
        user.numero_documento = request.POST.get('numero_documento', user.numero_documento)
        user.telefono = request.POST.get('telefono', user.telefono)
        user.residencia = request.POST.get('residencia', user.residencia)
        user.rol = rol
        user.es_guia = (rol == Usuario.Roles.GUIA)
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
            messages.error(request, 'El nombre de usuario y el email son obligatorios.')
            return redirect('gestion_usuarios')
        if Usuario.objects.filter(username=username).exists():
            messages.error(request, f'El usuario «{username}» ya existe.')
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
            es_guia=(rol == Usuario.Roles.GUIA),
            is_staff=(rol == Usuario.Roles.ADMIN),
        )
        password = request.POST.get('password', '').strip()
        user.set_password(password if password else request.POST.get('numero_documento', username))
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
        perfil.licencia_turismo = request.POST.get('licencia_turismo', perfil.licencia_turismo)
        experiencia = request.POST.get('experiencia_anos', '0')
        perfil.experiencia_anos = int(experiencia) if experiencia.isdigit() else 0
        perfil.biografia = request.POST.get('biografia', perfil.biografia)
        perfil.save()

    accion = 'actualizado' if user_id else 'registrado'
    messages.success(request, f'Usuario «{user.get_full_name()}» {accion} correctamente.')
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
    guias = Usuario.objects.filter(rol=Usuario.Roles.GUIA).select_related('guia')
    guias_activos = guias.filter(is_active=True).count()
    guia_seleccionado = None
    if id:
        guia_seleccionado = get_object_or_404(Usuario, id=id, rol=Usuario.Roles.GUIA)
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
            user.es_guia = True
            user.save()
            GuiaTuristico.objects.get_or_create(usuario=user)
            messages.success(request, f'Rol de guía asignado a {user.username}')
        else:
            user.rol = Usuario.Roles.CLIENTE
            user.es_guia = False
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
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.email = request.POST.get('email', user.email)
        user.tipo_documento = request.POST.get('tipo_documento', user.tipo_documento)
        user.numero_documento = request.POST.get('numero_documento', user.numero_documento)
        user.telefono = request.POST.get('telefono', user.telefono)
        user.residencia = request.POST.get('residencia', user.residencia)
        if 'imagen_perfil' in request.FILES:
            user.imagen_perfil = request.FILES['imagen_perfil']
        user.save()

        perfil, _ = GuiaTuristico.objects.get_or_create(usuario=user)
        perfil.licencia_turismo = request.POST.get('licencia_turismo', perfil.licencia_turismo)
        experiencia = request.POST.get('experiencia_anos')
        if experiencia and experiencia.isdigit():
            perfil.experiencia_anos = int(experiencia)
        perfil.biografia = request.POST.get('biografia', perfil.biografia)
        perfil.save()
        messages.success(request, f'Guía «{user.get_full_name()}» actualizado correctamente.')

    else:
        # --- MODO CREACIÓN ---
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()

        if not username or not email:
            messages.error(request, 'El nombre de usuario y el email son obligatorios.')
            return redirect('gestion_guias')

        if Usuario.objects.filter(username=username).exists():
            messages.error(request, f'El nombre de usuario «{username}» ya está en uso.')
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
            es_guia=True,
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
        messages.success(request, f'Guía «{user.get_full_name()}» registrado exitosamente.')

    return redirect('gestion_guias')

# 5. MÓDULO DE INTERACCIÓN / COMENTARIOS

@login_required
def enviar_comentario(request):
    """Renderiza el histórico de opiniones y procesa las nuevas reseñas de paquetes."""
    if request.method == 'POST':
        tipo = request.POST.get('tipo', 'experiencia')
        titulo = request.POST.get('titulo')
        mensaje = request.POST.get('mensaje')
        valoracion = request.POST.get('valoracion', 5)
        paquete_id = request.POST.get('paquete_id')
        
        Comentario.objects.create(
            usuario=request.user,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            valoracion=valoracion,
            paquete_id=paquete_id if paquete_id else None
        )
        messages.success(request, 'Comentario enviado exitosamente.')
        return redirect('mis_resenas')

    return render(request, 'private/comentarios.html', {
        'titulo': 'Comunidad Monagua — Reseñas y Experiencias'
    })

# 6. ADMINISTRACIÓN DE COMENTARIOS

@user_passes_test(lambda u: u.is_staff)
def listar_comentarios(request):
    """Renderiza el módulo de moderación y auditoría de comentarios para el Staff."""
    comentarios = Comentario.objects.all().select_related('usuario', 'paquete').order_by('-fecha_creacion')
    return render(request, 'admin/comentarios.html', {
        'titulo': 'Moderación de Comentarios — Administración',
        'comentarios': comentarios
    })

@user_passes_test(lambda u: u.is_staff)
def toggle_visible(request, pk):
    """Acción de backend para alternar la visibilidad pública de un comentario (Redirecciona)."""
    if request.method == 'POST':
        comentario = get_object_or_404(Comentario, pk=pk)
        comentario.visible = not comentario.visible
        comentario.save()
        estado = 'visible' if comentario.visible else 'oculto'
        messages.info(request, f'Comentario marcado como {estado}.')
    return redirect('listar_comentarios')

@user_passes_test(lambda u: u.is_staff)
def responder_comentario(request, pk):
    """Acción de backend para almacenar la respuesta oficial del administrador (Redirecciona)."""
    if request.method == 'POST':
        comentario = get_object_or_404(Comentario, pk=pk)
        comentario.admin_respuesta = request.POST.get('admin_respuesta', '')
        comentario.save()
        messages.success(request, 'Respuesta guardada correctamente.')
    return redirect('listar_comentarios')

# 7. HISTORIAL Y RESEÑAS DE USUARIOS

@login_required
def mis_resenas_view(request):
    """
    Renderiza el panel de reseñas del turista.
    Procesa el envío de nuevas experiencias y distribuye las métricas globales.
    """
    if request.method == 'POST':
        tipo = request.POST.get('tipo', 'experiencia')
        titulo = request.POST.get('titulo')
        mensaje = request.POST.get('mensaje')
        valoracion = request.POST.get('valoracion', 5)
        paquete_id = request.POST.get('paquete_id')
        
        Comentario.objects.create(
            usuario=request.user,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            valoracion=valoracion,
            paquete_id=paquete_id if paquete_id else None
        )
        messages.success(request, 'Gracias por tu reseña.')
        return redirect('mis_resenas')

    comentarios = Comentario.objects.filter(usuario=request.user).order_by('-fecha_creacion')
    return render(request, 'private/resenas.html', {
        'titulo': 'Mis Experiencias y Reseñas — Monagua',
        'comentarios': comentarios
    })

# 8. MÓDULO DE MÉTRICAS Y ESTADÍSTICAS

@user_passes_test(lambda u: u.is_staff)
def estadisticas_admin(request):
    """
    Renderiza el panel de control global (Dashboard) para el Administrador.
    Calcula consolidados de reservas, auditoría de pagos, distribución de 
    calificaciones y el feed de actividad reciente del sistema.
    """
    total_usuarios = Usuario.objects.count()
    promedio_calificacion = Comentario.objects.aggregate(Avg('valoracion'))['valoracion__avg']
    
    return render(request, 'admin/estadisticas_admin.html', {
        'titulo': 'Métricas Globales — Panel de Administración',
        'nivel_viajero': 'Director de Expediciones',
        'total_usuarios': total_usuarios,
        'promedio_calificacion': promedio_calificacion or 0
    })

@login_required
def estadisticas_turista(request):
    """
    Renderiza el historial métrico personalizado del Turista.
    Muestra la inversión total del usuario, el estado de sus reservas, sus PQRS 
    y calcula dinámicamente su nivel de viajero según sus experiencias completadas.
    """
    comentarios_count = Comentario.objects.filter(usuario=request.user).count()
    
    if comentarios_count >= 10:
        nivel_viajero = 'Expedicionista'
    elif comentarios_count >= 5:
        nivel_viajero = 'Aventurero'
    elif comentarios_count >= 1:
        nivel_viajero = 'Explorador'
    else:
        nivel_viajero = 'Viajero Novel'
        
    return render(request, 'private/estadisticas.html', {
        'titulo': 'Mis Estadísticas de Viaje — Monagua',
        'nivel_viajero': nivel_viajero,
        'comentarios_count': comentarios_count
    })
