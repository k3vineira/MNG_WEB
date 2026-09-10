from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from App.models import Usuario
from App.utils import crear_notificacion_sistema


def es_administrador(user):
    return user.is_authenticated and user.is_active and (user.is_staff or getattr(user, 'rol', None) == Usuario.Roles.ADMIN)


@login_required
def panel_rapido_view(request):
    if not getattr(request.user, 'es_turista', False):
        if request.user.is_staff or getattr(request.user, 'rol', None) == Usuario.Roles.ADMIN:
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
    """Directorio y gestión de cuentas de usuario en el panel de administración."""
    filtro = request.GET.get('filtro', '').strip()
    query = request.GET.get('q', '').strip()

    usuarios = Usuario.objects.all().order_by('-id')

    if filtro:
        usuarios = usuarios.filter(rol=filtro)

    if query:
        usuarios = usuarios.filter(
            Q(username__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(numero_documento__icontains=query)
        )

    total_admins = Usuario.objects.filter(rol=Usuario.Roles.ADMIN).count()
    total_guias = Usuario.objects.filter(rol=Usuario.Roles.GUIA).count()
    total_clientes = Usuario.objects.filter(rol=Usuario.Roles.CLIENTE).count()

    contexto = {
        'usuarios': usuarios,
        'filtro_actual': filtro,
        'total_admins': total_admins,
        'total_guias': total_guias,
        'total_clientes': total_clientes,
    }
    return render(request, 'admin/usuario/gestion_usuarios.html', contexto)


@user_passes_test(es_administrador)
def usuarios_guardar(request):
    """Crea o actualiza la información y rol de un usuario."""
    if request.method == 'POST':
        user_id = request.POST.get('id')
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        tipo_documento = request.POST.get('tipo_documento', 'CC').strip()
        numero_documento = request.POST.get('numero_documento', '').strip()
        residencia = request.POST.get('residencia', '').strip()
        rol = request.POST.get('rol', Usuario.Roles.CLIENTE).strip()
        password = request.POST.get('password', '').strip()
        imagen_perfil = request.FILES.get('imagen_perfil')

        if user_id:
            user_obj = get_object_or_404(Usuario, pk=user_id)
            user_obj.first_name = first_name
            user_obj.last_name = last_name
            if email:
                user_obj.email = email
            user_obj.telefono = telefono
            user_obj.tipo_documento = tipo_documento
            user_obj.numero_documento = numero_documento
            user_obj.residencia = residencia
            user_obj.rol = rol
            if rol == Usuario.Roles.ADMIN:
                user_obj.is_staff = True
            if password:
                user_obj.set_password(password)
            if imagen_perfil:
                user_obj.imagen_perfil = imagen_perfil
            user_obj.save()

            crear_notificacion_sistema(
                usuario=request.user,
                accion="USUARIO MODIFICADO",
                tabla_afectada="Usuario",
                observacion=f"Se actualizaron los datos del usuario '{user_obj.username}'.",
                valor_anterior="N/A",
                nuevo_valor=f"Usuario: {user_obj.username}, Rol: {user_obj.get_rol_display()}"
            )
            messages.success(request, f"Usuario '{user_obj.username}' actualizado correctamente.")
        else:
            username = request.POST.get('username', '').strip()
            if not username:
                username = email.split('@')[0] if email else f"user_{numero_documento}"

            if Usuario.objects.filter(username=username).exists():
                messages.error(request, f"El nombre de usuario '{username}' ya está en uso.")
                return redirect('gestion_usuarios')

            if email and Usuario.objects.filter(email=email).exists():
                messages.error(request, f"El correo '{email}' ya se encuentra registrado.")
                return redirect('gestion_usuarios')

            user_obj = Usuario.objects.create_user(
                username=username,
                email=email,
                password=password or 'Monagua2026*',
                first_name=first_name,
                last_name=last_name,
                rol=rol,
                telefono=telefono,
                tipo_documento=tipo_documento,
                numero_documento=numero_documento,
                residencia=residencia,
                is_staff=(rol == Usuario.Roles.ADMIN)
            )
            if imagen_perfil:
                user_obj.imagen_perfil = imagen_perfil
                user_obj.save()

            crear_notificacion_sistema(
                usuario=request.user,
                accion="NUEVO USUARIO CREADO",
                tabla_afectada="Usuario",
                observacion=f"Se creó la cuenta del usuario '{user_obj.username}'.",
                valor_anterior="Ninguno",
                nuevo_valor=f"Usuario: {user_obj.username}, Rol: {user_obj.get_rol_display()}"
            )
            messages.success(request, f"Usuario '{user_obj.username}' creado exitosamente.")

    return redirect('gestion_usuarios')


@user_passes_test(es_administrador)
def usuarios_toggle_estado(request, id):
    """Activa o desactiva la cuenta de un usuario."""
    if request.method == 'POST':
        user_obj = get_object_or_404(Usuario, pk=id)
        if user_obj.id == request.user.id:
            messages.error(request, "No puedes desactivar tu propia cuenta de administrador.")
            return redirect('gestion_usuarios')

        user_obj.is_active = not user_obj.is_active
        user_obj.save()

        estado_txt = "activada" if user_obj.is_active else "desactivada"
        crear_notificacion_sistema(
            usuario=request.user,
            accion="ESTADO DE USUARIO MODIFICADO",
            tabla_afectada="Usuario",
            observacion=f"La cuenta del usuario '{user_obj.username}' fue {estado_txt}.",
            valor_anterior="N/A",
            nuevo_valor=f"Estado: {estado_txt}"
        )
        messages.success(request, f"La cuenta de '{user_obj.username}' ha sido {estado_txt}.")

    return redirect('gestion_usuarios')