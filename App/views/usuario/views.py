from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.contrib import messages
from App.models import Usuario
from App.utils import crear_notificacion_sistema


def es_administrador(user):
    return user.is_authenticated and user.is_active and (user.is_staff or user.rol == Usuario.Roles.ADMIN)


@login_required
def panel_rapido_view(request):
    if not request.user.es_turista:
        if request.user.is_staff or request.user.rol == Usuario.Roles.ADMIN:
            return redirect('dashboard_admin')
        return redirect('index')

    return render(request, 'partials/panel_rapido.html')


@login_required
def perfil_turista_view(request):
    """Renderiza y gestiona la actualización del perfil del turista/cliente."""
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
        messages.success(request, 'Tu perfil ha sido actualizado correctamente.')
        return redirect('perfil_detalles')

    return render(request, 'usuario/perfil_turista.html', {'user': user})


# ==============================================================================
# GESTIÓN DE USUARIOS (ADMINISTRACIÓN)
# ==============================================================================

@user_passes_test(es_administrador)
def gestion_usuarios_admin(request):
    """Listado, filtrado y búsqueda general de usuarios en el panel administrativo."""
    usuarios = Usuario.objects.all().order_by('-id')

    filtro_actual = request.GET.get('filtro', '').strip().upper()
    if filtro_actual == 'ADMIN':
        usuarios = usuarios.filter(rol=Usuario.Roles.ADMIN)
    elif filtro_actual == 'GUIA':
        usuarios = usuarios.filter(rol=Usuario.Roles.GUIA)
    elif filtro_actual == 'CLIENTE':
        usuarios = usuarios.filter(rol=Usuario.Roles.CLIENTE)

    q = request.GET.get('q', '').strip()
    if q:
        usuarios = usuarios.filter(
            Q(username__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q) |
            Q(email__icontains=q) |
            Q(numero_documento__icontains=q)
        )

    total_admins = Usuario.objects.filter(rol=Usuario.Roles.ADMIN).count()
    total_guias = Usuario.objects.filter(rol=Usuario.Roles.GUIA).count()
    total_clientes = Usuario.objects.filter(rol=Usuario.Roles.CLIENTE).count()

    contexto = {
        'usuarios': usuarios,
        'total_admins': total_admins,
        'total_guias': total_guias,
        'total_clientes': total_clientes,
        'filtro_actual': filtro_actual,
    }
    return render(request, 'admin/usuario/gestion_usuarios.html', contexto)


@user_passes_test(es_administrador)
def usuarios_guardar(request):
    """Guarda modificaciones de un usuario existente desde el panel de administración."""
    if request.method == 'POST':
        user_id = request.POST.get('id')
        user_obj = get_object_or_404(Usuario, pk=user_id)

        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        tipo_documento = request.POST.get('tipo_documento', '').strip()
        numero_documento = request.POST.get('numero_documento', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        residencia = request.POST.get('residencia', '').strip()
        password = request.POST.get('password', '').strip()
        rol_str = request.POST.get('rol', '').strip().upper()
        imagen_perfil = request.FILES.get('imagen_perfil')

        user_obj.first_name = first_name
        user_obj.last_name = last_name
        if email:
            user_obj.email = email
        if tipo_documento:
            user_obj.tipo_documento = tipo_documento
        user_obj.numero_documento = numero_documento
        user_obj.telefono = telefono
        user_obj.residencia = residencia

        if password:
            user_obj.set_password(password)

        if imagen_perfil:
            user_obj.imagen_perfil = imagen_perfil

        # Cambio de rol (respetando que no se degrade el admin a sí mismo sin permiso)
        if user_obj.id != request.user.id and rol_str:
            if rol_str == 'ADMIN':
                user_obj.rol = Usuario.Roles.ADMIN
                user_obj.is_staff = True
            elif rol_str == 'GUIA':
                user_obj.rol = Usuario.Roles.GUIA
                user_obj.is_staff = False
            elif rol_str == 'CLIENTE':
                user_obj.rol = Usuario.Roles.CLIENTE
                user_obj.is_staff = False

        user_obj.save()

        crear_notificacion_sistema(
            usuario=request.user,
            accion="USUARIO MODIFICADO",
            tabla_afectada="Usuario",
            observacion=f"El perfil del usuario '{user_obj.username}' fue actualizado desde el panel de administración.",
            valor_anterior="N/A",
            nuevo_valor=f"Nombre: {user_obj.get_full_name()}, Rol: {user_obj.get_rol_display()}"
        )

        messages.success(request, f"Usuario '{user_obj.username}' actualizado con éxito.")

    return redirect('gestion_usuarios')


@user_passes_test(es_administrador)
def usuarios_toggle_estado(request, id):
    """Activa o inactiva a un usuario."""
    if request.method == 'POST':
        user_obj = get_object_or_404(Usuario, pk=id)
        if user_obj.id == request.user.id:
            messages.error(request, "No puedes desactivar tu propia cuenta de administrador.")
            return redirect('gestion_usuarios')

        user_obj.is_active = not user_obj.is_active
        user_obj.save()

        estado_str = "activado" if user_obj.is_active else "inactivado"
        crear_notificacion_sistema(
            usuario=request.user,
            accion=f"USUARIO {estado_str.upper()}",
            tabla_afectada="Usuario",
            observacion=f"El usuario '{user_obj.username}' fue {estado_str}.",
            valor_anterior=f"Activo: {not user_obj.is_active}",
            nuevo_valor=f"Activo: {user_obj.is_active}"
        )
        messages.success(request, f"El usuario '{user_obj.username}' ha sido {estado_str} correctamente.")

    return redirect('gestion_usuarios')


  