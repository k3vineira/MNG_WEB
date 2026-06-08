from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.contrib import messages
from django.db.models import Count, Avg, Sum

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
def gestion_guias(request, id=None):
    """Renderiza el panel de control y auditoría para la gestión de Guías."""
    guias = Usuario.objects.filter(rol=Usuario.Roles.GUIA).select_related('guia')
    guia_seleccionado = None
    if id:
        guia_seleccionado = get_object_or_404(Usuario, id=id, rol=Usuario.Roles.GUIA)

    return render(request, 'admin/index-guias.html', {
        'titulo': 'Panel de Gestión de Guías — Administración',
        'guias': guias,
        'guia_seleccionado': guia_seleccionado
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
def guias_baja_reactivar(request, id, estado):
    """Acción de backend para suspender o reactivar cuentas de guías (Redirecciona)."""
    if request.method == 'POST':
        guia = get_object_or_404(Usuario, id=id, rol=Usuario.Roles.GUIA)
        if estado == 'baja':
            guia.is_active = False
            messages.warning(request, f'Guía {guia.username} dado de baja.')
        elif estado == 'reactivar':
            guia.is_active = True
            messages.success(request, f'Guía {guia.username} reactivado.')
        guia.save()
    return redirect('gestion_guias')

@user_passes_test(lambda u: u.is_staff)
def guias_guardar(request):
    """Acción de backend para salvar modificaciones del perfil del guía (Redirecciona)."""
    if request.method == 'POST':
        guia_id = request.POST.get('id')
        if guia_id:
            guia = get_object_or_404(Usuario, id=guia_id, rol=Usuario.Roles.GUIA)
            guia.first_name = request.POST.get('first_name', guia.first_name)
            guia.last_name = request.POST.get('last_name', guia.last_name)
            guia.email = request.POST.get('email', guia.email)
            guia.save()

            guia_perfil = getattr(guia, 'guia', None)
            if guia_perfil:
                guia_perfil.licencia_turismo = request.POST.get('licencia_turismo', guia_perfil.licencia_turismo)
                experiencia = request.POST.get('experiencia_anos')
                if experiencia and experiencia.isdigit():
                    guia_perfil.experiencia_anos = int(experiencia)
                guia_perfil.biografia = request.POST.get('biografia', guia_perfil.biografia)
                guia_perfil.save()
            messages.success(request, 'Datos del guía actualizados correctamente.')
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

