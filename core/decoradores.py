from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from usuarios.models import Usuario

def requiere_autenticacion(vista_func):
    """
    Decorador para asegurar que el usuario esté autenticado.
    Si no está autenticado, lo redirige al inicio de sesión.
    """
    @wraps(vista_func)
    def _wrapper(request, *args, **kwargs):
        """
        _wrapper.
        
        :param request: Descripción del parámetro.
        
        :param args: Descripción del parámetro.
        
        :param kwargs: Descripción del parámetro.
        
        :return: Respuesta de la función.
        """
        if not request.user.is_authenticated:
            messages.warning(request, "Debes iniciar sesión para acceder a esta página.")
            return redirect('login')
        return vista_func(request, *args, **kwargs)
    return _wrapper


def requiere_administrador(vista_func):
    """
    Decorador para asegurar que el usuario tenga el rol de Administrador (o sea staff).
    Si no cumple, se le deniega el acceso (Error 403 - PermissionDenied).
    """
    @wraps(vista_func)
    def _wrapper(request, *args, **kwargs):
        """
        _wrapper.
        
        :param request: Descripción del parámetro.
        
        :param args: Descripción del parámetro.
        
        :param kwargs: Descripción del parámetro.
        
        :return: Respuesta de la función.
        """
        # Primero asegurar que esté autenticado
        if not request.user.is_authenticated:
            messages.warning(request, "Debes iniciar sesión para acceder a esta página.")
            return redirect('login')
        
        # Verificar si es staff o tiene el rol de ADMIN
        if request.user.is_staff or request.user.rol == Usuario.Roles.ADMIN:
            return vista_func(request, *args, **kwargs)
        
        raise PermissionDenied("No tienes permisos de Administrador para acceder a esta sección.")
    return _wrapper


def requiere_guia(vista_func):
    """
    Decorador para asegurar que el usuario tenga el rol de Guía Turístico o Administrador.
    Si no cumple, se le deniega el acceso.
    """
    @wraps(vista_func)
    def _wrapper(request, *args, **kwargs):
        """
        _wrapper.
        
        :param request: Descripción del parámetro.
        
        :param args: Descripción del parámetro.
        
        :param kwargs: Descripción del parámetro.
        
        :return: Respuesta de la función.
        """
        if not request.user.is_authenticated:
            messages.warning(request, "Debes iniciar sesión para acceder a esta página.")
            return redirect('login')
        
        # Los guías y los administradores tienen acceso a las vistas de guía
        if request.user.es_guia or request.user.is_staff or request.user.rol == Usuario.Roles.ADMIN:
            return vista_func(request, *args, **kwargs)
        
        raise PermissionDenied("Solo los Guías Turísticos pueden acceder a esta sección.")
    return _wrapper


def requiere_cliente(vista_func):
    """
    Decorador para asegurar que el usuario sea un Cliente/Turista.
    Si no cumple, se le deniega el acceso.
    """
    @wraps(vista_func)
    def _wrapper(request, *args, **kwargs):
        """
        _wrapper.
        
        :param request: Descripción del parámetro.
        
        :param args: Descripción del parámetro.
        
        :param kwargs: Descripción del parámetro.
        
        :return: Respuesta de la función.
        """
        if not request.user.is_authenticated:
            messages.warning(request, "Debes iniciar sesión para acceder a esta página.")
            return redirect('login')
        
        if request.user.es_turista or request.user.is_staff or request.user.rol == Usuario.Roles.ADMIN:
            return vista_func(request, *args, **kwargs)
        
        raise PermissionDenied("Esta sección está reservada para Clientes/Turistas.")
    return _wrapper
