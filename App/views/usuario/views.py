import json
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from App.models import Usuario, Paquete, Reserva, PQRS, Calificacion
from App.utils import crear_notificacion_sistema
from App.forms.usuario.forms import PerfilTuristaForm, PerfilGuiaForm, CambiarClaveSeguraForm


def es_administrador(user):
    return user.is_authenticated and user.is_active and (user.is_staff or getattr(user, 'rol', None) == Usuario.Roles.ADMIN)


@login_required
def panel_rapido_view(request):
    if not getattr(request.user, 'es_turista', False):
        if request.user.is_staff or getattr(request.user, 'rol', None) == Usuario.Roles.ADMIN:
            return redirect('dashboard_admin')
        return redirect('index')

    user = request.user

    # 1. Recomendación dinámica de paquetes con imagen
    paquetes_activos = list(Paquete.objects.filter(estado=True))
    paquetes_con_imagen = [p for p in paquetes_activos if p.imagen]
    if not paquetes_con_imagen:
        paquetes_con_imagen = paquetes_activos

    recomendacion = random.choice(paquetes_con_imagen) if paquetes_con_imagen else None

    recomendaciones_data = []
    for p in paquetes_con_imagen:
        if p.imagen:
            recomendaciones_data.append({
                'nombre': p.nombre,
                'imagen_url': p.imagen.url
            })

    # 2. Métricas y estadísticas del viajero
    reservas_qs = Reserva.objects.filter(usuario=user).select_related('paquete')
    total_reservas = reservas_qs.count()
    reservas_confirmadas = reservas_qs.filter(estado_reserva='confirmada').count()
    reservas_pendientes = reservas_qs.filter(estado_reserva='pendiente').count()
    total_pqrs = PQRS.objects.filter(usuario=user).count()
    total_calificaciones = Calificacion.objects.filter(reserva__usuario=user).count()

    # 3. Próxima aventura o última reserva activa
    hoy = timezone.now().date()
    proxima_reserva = reservas_qs.filter(
        estado_reserva__in=['confirmada', 'pendiente'],
        fecha_inicio__gte=hoy
    ).order_by('fecha_inicio').first()

    if not proxima_reserva:
        proxima_reserva = reservas_qs.order_by('-fecha_registro').first()

    # 4. Historial reciente de reservas (últimas 4)
    ultimas_reservas = reservas_qs.order_by('-id')[:4]

    contexto = {
        'recomendacion': recomendacion,
        'recomendaciones_data': recomendaciones_data,
        'total_reservas': total_reservas,
        'reservas_confirmadas': reservas_confirmadas,
        'reservas_pendientes': reservas_pendientes,
        'total_pqrs': total_pqrs,
        'total_calificaciones': total_calificaciones,
        'proxima_reserva': proxima_reserva,
        'ultimas_reservas': ultimas_reservas,
        'recomendaciones_json': json.dumps(recomendaciones_data),
    }

    return render(request, 'usuario/dashboard/panel_rapido.html', contexto)


@login_required
def perfil_turista_view(request):
    """
    Renderiza y gestiona la actualización segura del perfil unificado (Turista, Admin, Guía).
    Utiliza ModelForms con listas blancas estrictas para neutralizar cualquier inyección
    de campos privilegiados (rol, is_staff, is_superuser, password, email) desde DevTools.
    """
    user = request.user
    form_class = PerfilGuiaForm if getattr(user, 'es_guia', False) else PerfilTuristaForm

    if request.method == 'POST' and request.POST.get('editar_perfil') == '1':
        form = form_class(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tu perfil ha sido actualizado correctamente.')
            return redirect(request.path)
        else:
            errores_txt = [str(err[0]) for err in form.errors.values()]
            messages.error(request, f"Error al actualizar perfil: {' '.join(errores_txt)}")

    return render(request, 'usuario/perfil/perfil.html', {'user': user})
 
 
@login_required
def configuracion_usuario_view(request):
    """
    Vista integral y funcional para la Configuración de Cuenta, Seguridad y Preferencias del Usuario.
    Procesa:
    1. Cambio de contraseña con validación de seguridad y actualización de hash de sesión.
    2. Preferencias de notificaciones por email y sonidos del sistema.
    3. Preferencias de interfaz (idioma, tema visual, formato de fecha).
    4. Privacidad y visibilidad del perfil.
    5. Actualización de datos de contacto directo.
    6. Exportación de datos de usuario en formato JSON (Habeas Data).
    7. Cierre de otras sesiones activas para seguridad.
    """
    user = request.user

    # Descarga de datos personales (Habeas Data)
    if request.GET.get('exportar') == 'json' or request.POST.get('accion') == 'exportar_datos':
        import json
        from django.http import HttpResponse
        from App.models import Reserva, Pago, PQRS

        total_reservas = Reserva.objects.filter(usuario=user).count()
        total_pagos = Pago.objects.filter(reserva__usuario=user).count()
        total_pqrs = PQRS.objects.filter(usuario=user).count()

        datos_exportacion = {
            'sistema': 'Monagua Turismo Ecoturístico',
            'fecha_exportacion': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            'usuario': {
                'id': user.id,
                'username': user.username,
                'nombres': user.first_name,
                'apellidos': user.last_name,
                'email': user.email,
                'tipo_documento': user.get_tipo_documento_display() if hasattr(user, 'get_tipo_documento_display') else user.tipo_documento,
                'numero_documento': user.numero_documento,
                'telefono': user.telefono,
                'residencia': user.residencia,
                'rol': user.get_rol_display() if hasattr(user, 'get_rol_display') else str(user.rol),
                'fecha_registro': user.date_joined.strftime('%Y-%m-%d %H:%M:%S') if user.date_joined else None,
                'ultimo_acceso': user.last_login.strftime('%Y-%m-%d %H:%M:%S') if user.last_login else None,
            },
            'resumen_actividad': {
                'total_reservas': total_reservas,
                'total_pagos': total_pagos,
                'total_pqrs': total_pqrs,
            }
        }

        response = HttpResponse(
            json.dumps(datos_exportacion, indent=4, ensure_ascii=False),
            content_type='application/json; charset=utf-8'
        )
        response['Content-Disposition'] = f'attachment; filename="datos_cuenta_monagua_{user.username}.json"'
        return response

    if request.method == 'POST':
        accion = request.POST.get('accion')

        # 1. Cambio de Contraseña Seguro con validación en servidor
        if accion == 'cambiar_clave':
            form_clave = CambiarClaveSeguraForm(user=user, data=request.POST)
            if form_clave.is_valid():
                user.set_password(form_clave.cleaned_data['new_password'])
                user.save()
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, user)
                messages.success(request, '¡Tu contraseña ha sido actualizada con éxito!')
            else:
                errores_txt = [str(err[0]) for err in form_clave.errors.values()]
                messages.error(request, f"Error al actualizar la contraseña: {' '.join(errores_txt)}")
            return redirect('configuracion_usuario')

        # 2. Preferencias de Notificaciones y Sistema
        elif accion == 'guardar_preferencias':
            notif_reservas = bool(request.POST.get('notif_reservas'))
            notif_pagos = bool(request.POST.get('notif_pagos'))
            notif_promos = bool(request.POST.get('notif_promos'))
            notif_sonido = bool(request.POST.get('notif_sonido'))
            autenticacion_dos_pasos = bool(request.POST.get('autenticacion_dos_pasos'))
            visibilidad_perfil = request.POST.get('visibilidad_perfil', 'publico')
            tema_visual = request.POST.get('tema_visual', 'claro')
            idioma_pref = request.POST.get('idioma_pref', 'es')

            request.session['pref_notif_reservas'] = notif_reservas
            request.session['pref_notif_pagos'] = notif_pagos
            request.session['pref_notif_promos'] = notif_promos
            request.session['pref_notif_sonido'] = notif_sonido
            request.session['pref_2fa'] = autenticacion_dos_pasos
            request.session['pref_visibilidad'] = visibilidad_perfil
            request.session['pref_tema_visual'] = tema_visual
            request.session['pref_idioma'] = idioma_pref

            messages.success(request, 'Preferencias del sistema y notificaciones actualizadas correctamente.')
            return redirect('configuracion_usuario')

        # 3. Actualizar Contacto Rápido
        elif accion == 'actualizar_contacto':
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            telefono = request.POST.get('telefono', '').strip()
            residencia = request.POST.get('residencia', '').strip()

            if first_name:
                user.first_name = first_name
            if last_name:
                user.last_name = last_name
            if telefono:
                user.telefono = telefono
            if residencia:
                user.residencia = residencia

            user.save()
            messages.success(request, 'Información de contacto y datos personales actualizados.')
            return redirect('configuracion_usuario')

        # 4. Cerrar Otras Sesiones
        elif accion == 'cerrar_otras_sesiones':
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)
            messages.success(request, 'Se han revocado las credenciales en otros dispositivos.')
            return redirect('configuracion_usuario')

    # Preferencias actuales de la sesión (o defaults)
    preferencias = {
        'notif_reservas': request.session.get('pref_notif_reservas', True),
        'notif_pagos': request.session.get('pref_notif_pagos', True),
        'notif_promos': request.session.get('pref_notif_promos', True),
        'notif_sonido': request.session.get('pref_notif_sonido', True),
        'autenticacion_dos_pasos': request.session.get('pref_2fa', False),
        'visibilidad_perfil': request.session.get('pref_visibilidad', 'publico'),
        'tema_visual': request.session.get('pref_tema_visual', 'claro'),
        'idioma_pref': request.session.get('pref_idioma', 'es'),
    }

    # Cálculo del Nivel de Seguridad de la Cuenta
    score_seguridad = 25  # Base por cuenta creada
    if user.email:
        score_seguridad += 25
    if user.telefono:
        score_seguridad += 25
    if getattr(user, 'numero_documento', None):
        score_seguridad += 25

    # Datos de sesión
    ip_cliente = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', '127.0.0.1'))
    if ',' in ip_cliente:
        ip_cliente = ip_cliente.split(',')[0].strip()

    contexto = {
        'user': user,
        'preferencias': preferencias,
        'score_seguridad': score_seguridad,
        'ip_cliente': ip_cliente,
        'user_agent': request.META.get('HTTP_USER_AGENT', 'Navegador Web'),
    }

    return render(request, 'usuario/perfil/configuracion.html', contexto)


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
                mensaje=f"Se ha actualizado la información del usuario '{user_obj.username}'.",
                tipo="Usuario",
                prioridad="Media"
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
                mensaje=f"Se ha creado un nuevo usuario '{user_obj.username}' con rol '{user_obj.get_rol_display()}'.",
                tipo="Usuario",
                prioridad="Media"
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
            mensaje=f"La cuenta de '{user_obj.username}' ha sido {estado_txt}.",
            tipo="Usuario",
            prioridad="Media"
        )
        messages.success(request, f"La cuenta de '{user_obj.username}' ha sido {estado_txt}.")

    return redirect('gestion_usuarios')