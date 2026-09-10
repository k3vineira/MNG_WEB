from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from App.models import Usuario
from App.utils import crear_notificacion_sistema


def es_administrador(user):
    return user.is_authenticated and user.is_active and (user.is_staff or user.rol == Usuario.Roles.ADMIN)


# ==============================================================================
# GESTIÓN DE GUÍAS TURÍSTICOS (ADMINISTRACIÓN)
# ==============================================================================

@user_passes_test(es_administrador)
def gestion_guias_view(request):
    """Directorio y gestión de guías turísticos."""
    guias = Usuario.objects.filter(rol=Usuario.Roles.GUIA).order_by('-id')
    guias_activos = guias.filter(is_active=True).count()

    contexto = {
        'guias': guias,
        'guias_activos': guias_activos,
    }
    return render(request, 'admin/guias/gestion_guias.html', contexto)


@user_passes_test(es_administrador)
def guias_guardar(request):
    """Registra o actualiza la información y credenciales de un guía turístico."""
    if request.method == 'POST':
        user_id = request.POST.get('id') or request.POST.get('guia_id')
        first_name = request.POST.get('first_name') or request.POST.get('nombre', '')
        last_name = request.POST.get('last_name') or request.POST.get('apellido', '')
        email = request.POST.get('email') or request.POST.get('correo', '')
        telefono = request.POST.get('telefono', '').strip()
        tipo_documento = request.POST.get('tipo_documento', 'CC').strip()
        numero_documento = request.POST.get('numero_documento') or request.POST.get('documento', '')
        residencia = request.POST.get('residencia', '').strip()
        tarjeta_profesional = request.POST.get('numero_tarjeta_profesional', '').strip()
        experiencia_anos_raw = request.POST.get('experiencia_anos') or request.POST.get('experiencia', 0)
        descripcion_experiencia = request.POST.get('descripcion_experiencia', '').strip()
        entidad_salud = request.POST.get('entidad_salud', '').strip()
        password = request.POST.get('password', '').strip()
        imagen_perfil = request.FILES.get('imagen_perfil')

        try:
            experiencia_anos = int(experiencia_anos_raw) if experiencia_anos_raw else 0
        except (ValueError, TypeError):
            experiencia_anos = 0

        if user_id:
            # Actualización
            user_obj = get_object_or_404(Usuario, pk=user_id)
            user_obj.first_name = first_name.strip()
            user_obj.last_name = last_name.strip()
            if email:
                user_obj.email = email.strip()
            user_obj.telefono = telefono
            user_obj.tipo_documento = tipo_documento
            user_obj.numero_documento = numero_documento.strip()
            user_obj.residencia = residencia
            user_obj.numero_tarjeta_profesional = tarjeta_profesional
            user_obj.experiencia_anos = experiencia_anos
            user_obj.descripcion_experiencia = descripcion_experiencia
            user_obj.entidad_salud = entidad_salud
            user_obj.rol = Usuario.Roles.GUIA

            if password:
                user_obj.set_password(password)

            if imagen_perfil:
                user_obj.imagen_perfil = imagen_perfil

            user_obj.save()

            crear_notificacion_sistema(
                usuario=request.user,
                accion="GUÍA MODIFICADO",
                tabla_afectada="Usuario",
                observacion=f"Se actualizaron los datos del guía '{user_obj.get_full_name() or user_obj.username}'.",
                valor_anterior="N/A",
                nuevo_valor=f"Guía: {user_obj.get_full_name()}, Licencia: {tarjeta_profesional}"
            )
            messages.success(request, f"Guía '{user_obj.get_full_name() or user_obj.username}' actualizado correctamente.")
        else:
            # Nuevo Registro
            username = request.POST.get('username', '').strip()
            if not username:
                username = email.split('@')[0] if email else f"guia_{numero_documento}"

            if Usuario.objects.filter(username=username).exists():
                messages.error(request, f"El nombre de usuario '{username}' ya está en uso.")
                return redirect('gestion_guias')

            if email and Usuario.objects.filter(email=email).exists():
                messages.error(request, f"El correo '{email}' ya se encuentra registrado.")
                return redirect('gestion_guias')

            user_obj = Usuario.objects.create_user(
                username=username,
                email=email,
                password=password or 'MonaguaGuia2026*',
                first_name=first_name.strip(),
                last_name=last_name.strip(),
                rol=Usuario.Roles.GUIA,
                telefono=telefono,
                tipo_documento=tipo_documento,
                numero_documento=numero_documento.strip(),
                residencia=residencia,
                numero_tarjeta_profesional=tarjeta_profesional,
                experiencia_anos=experiencia_anos,
                descripcion_experiencia=descripcion_experiencia,
                entidad_salud=entidad_salud,
            )

            if imagen_perfil:
                user_obj.imagen_perfil = imagen_perfil
                user_obj.save()

            crear_notificacion_sistema(
                usuario=request.user,
                accion="NUEVO GUÍA REGISTRADO",
                tabla_afectada="Usuario",
                observacion=f"Se dio de alta al guía turístico '{user_obj.get_full_name() or user_obj.username}'.",
                valor_anterior="Ninguno (Nuevo Registro)",
                nuevo_valor=f"Guía: {user_obj.get_full_name()}, Licencia: {tarjeta_profesional}"
            )
            messages.success(request, f"Guía '{user_obj.get_full_name() or user_obj.username}' registrado exitosamente.")

    return redirect('gestion_guias')


@user_passes_test(es_administrador)
def asignar_rol_guia(request, id):
    """Alterna el rol de un usuario entre Guía Turístico y Cliente."""
    if request.method == 'POST':
        user_obj = get_object_or_404(Usuario, pk=id)
        if user_obj.id == request.user.id:
            messages.error(request, "No puedes alterar tu propio rol de administrador.")
            return redirect('gestion_guias')

        if user_obj.rol == Usuario.Roles.GUIA:
            user_obj.rol = Usuario.Roles.CLIENTE
            accion = "ROL DE GUÍA RETIRADO"
            msg = f"Se ha retirado el rol de guía a '{user_obj.username}' (ahora es Cliente/Turista)."
        else:
            user_obj.rol = Usuario.Roles.GUIA
            accion = "ROL DE GUÍA ASIGNADO"
            msg = f"Se ha asignado el rol de guía turístico a '{user_obj.username}'."

        user_obj.save()

        crear_notificacion_sistema(
            usuario=request.user,
            accion=accion,
            tabla_afectada="Usuario",
            observacion=msg,
            valor_anterior="N/A",
            nuevo_valor=f"Rol: {user_obj.get_rol_display()}"
        )
        messages.success(request, msg)

    return redirect('gestion_guias')
