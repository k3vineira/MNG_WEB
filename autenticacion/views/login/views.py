from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db.models import Q
from App.models import Usuario
from App.utils import crear_notificacion_sistema
from autenticacion.forms import IniciarSesionForm


def login_vista(request):
    """
    Gestiona el inicio de sesión de usuarios (administradores, clientes, guías).
    Permite autenticarse utilizando correo electrónico o nombre de usuario.
    """
    if request.user.is_authenticated:
        if request.user.is_staff or getattr(request.user, 'rol', None) == Usuario.Roles.ADMIN:
            return redirect('dashboard_admin')
        elif getattr(request.user, 'es_turista', False):
            return redirect('panel_rapido')
        return redirect('tours')

    if request.method == 'POST':
        usuario_input = (request.POST.get('username') or request.POST.get('usuario_o_email') or '').strip()
        password = request.POST.get('password', '')

        if usuario_input and password:
            user_obj = Usuario.objects.filter(
                Q(username__iexact=usuario_input) | Q(email__iexact=usuario_input)
            ).first()

            if user_obj:
                user = authenticate(request, username=user_obj.username, password=password)
                if user is not None:
                    if user.is_active:
                        login(request, user)
                        crear_notificacion_sistema(
                            usuario=user,
                            accion="LOGIN",
                            tabla_afectada="Usuarios",
                            observacion=f"El usuario '{user.username}' inició sesión correctamente."
                        )
                        messages.success(request, f"¡Bienvenido de nuevo, {user.first_name or user.username}!")
                        
                        next_url = request.GET.get('next') or request.POST.get('next')
                        if next_url:
                            return redirect(next_url)
                        
                        if user.is_staff or getattr(user, 'rol', None) == Usuario.Roles.ADMIN:
                            return redirect('dashboard_admin')
                        elif getattr(user, 'es_turista', False):
                            return redirect('panel_rapido')
                        return redirect('tours')
                    else:
                        messages.error(request, "Tu cuenta se encuentra desactivada. Por favor contacta al administrador.")
                else:
                    messages.error(request, "Contraseña incorrecta. Por favor inténtalo de nuevo.")
            else:
                messages.error(request, "No existe ningún usuario o correo registrado con esos datos.")
        else:
            messages.error(request, "Por favor completa todos los campos requeridos.")

    form = IniciarSesionForm()
    return render(request, 'autenticacion/login.html', {'form': form})


def logout_vista(request):
    """
    Cierra la sesión activa del usuario y redirige al inicio de la plataforma.
    Soporta peticiones GET y POST para evitar errores 405.
    """
    if request.user.is_authenticated:
        usuario_nombre = request.user.username
        crear_notificacion_sistema(
            usuario=request.user,
            accion="LOGOUT",
            tabla_afectada="Usuarios",
            observacion=f"El usuario '{usuario_nombre}' cerró sesión."
        )
        messages.info(request, "Has cerrado sesión correctamente. ¡Hasta pronto!")
    logout(request)
    return redirect('index')
