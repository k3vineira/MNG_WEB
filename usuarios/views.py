from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from .models import Usuario, Cliente
from .forms import RegistroForm


@login_required
def inicio_usuarios(request):
    """
    Punto de entrada tras el login. Redirige a los administradores al dashboard
    y a los turistas a su página de inicio personalizada.
    """
    if request.user.is_staff:
        return redirect('dashboard')

    context = {
        'titulo': 'Bienvenido a Monagua',
    }
    return render(request, 'turista/index_turista.html', context)


@user_passes_test(lambda u: u.is_staff, login_url='inicio')
def dashboard_admin(request):
    """
    Vista protegida para el Dashboard Administrativo.
    Solo accesible para usuarios con el atributo is_staff=True.
    """
    context = {
        'titulo': 'Tablero de Rendimiento',
        'total_ventas': 0.0,
        'total_usuarios': 0,
        'total_reservas': 0,
        'total_tours': 0,
        'total_promociones': 0,
        'ingresos_mensuales': [0]*12,
        'reservas_confirmadas': 0,
        'reservas_pendientes': 0,
        'reservas_canceladas': 0,
        'reservas_semana': [0]*7,
        'actividad_reciente': [],
    }
    return render(request, 'admin/index-admin.html', context)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('inicio')

    if request.method == 'POST':
        # Permitir login con correo interceptando los datos del POST
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
            user = authenticate(
                username=username,
                password=password
            )
            if user is not None:
                auth_login(request, user)
                messages.success(request, f"¡Bienvenido de nuevo, {user.username}!")

                # Redirigir a 'next' preservando parámetros adicionales como paquete_id
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
    """
    Cierra la sesión del usuario y redirige a la página de inicio de sesión.
    """
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

            # Crear el perfil de Cliente asociado
            Cliente.objects.create(usuario=user, pais=pais, ciudad=ciudad)

            messages.success(request, "¡Registro exitoso! Tu cuenta ha sido creada. Ahora puedes iniciar sesión.")
            
            # Preservar parámetros de redirección hacia el login
            from django.urls import reverse
            login_url = reverse('login')
            next_url = request.GET.get('next')
            paquete_id = request.GET.get('paquete_id')
            query_params = []
            if next_url: query_params.append(f"next={next_url}")
            if paquete_id: query_params.append(f"paquete_id={paquete_id}")
            if query_params:
                login_url += "?" + "&".join(query_params)
                
            return redirect(login_url)
        else:
            messages.error(request, "Hubo un error en el registro. Por favor, revisa los datos.")
    else:
        form = RegistroForm()

    return render(request, 'authentication/registro.html', {'form': form})


def terminos_view(request):
    """
    Vista pública para la página de Términos y Condiciones.
    Accesible sin necesidad de autenticación.
    """
    return render(request, 'public/terminos.html')


def nosotros_view(request):
    """
    Vista pública para la página Nosotros.
    Accesible sin necesidad de autenticación.
    """
    return render(request, 'public/nosotros.html')


@login_required
def perfil_view(request):
    """
    Vista para visualizar y actualizar el perfil del usuario.
    Maneja la actualización de imagen y datos personales desde el modal.
    """
    user = request.user

    if request.method == 'POST':
        # Caso 1: Actualización de foto de perfil
        if 'imagen_perfil' in request.FILES:
            user.imagen_perfil = request.FILES['imagen_perfil']
            user.save()
            messages.success(request, "¡Foto de perfil actualizada con éxito!")

        # Caso 2: Edición de datos personales (Modal)
        elif request.POST.get('editar_perfil') == '1':
            user.first_name = request.POST.get('first_name', user.first_name)
            user.last_name = request.POST.get('last_name', user.last_name)
            user.tipo_documento = request.POST.get('tipo_documento', user.tipo_documento)
            user.telefono = request.POST.get('telefono', user.telefono)
            user.residencia = request.POST.get('residencia', user.residencia)
            user.save()
            messages.success(request, "¡Información actualizada correctamente!")

        return redirect('detalles')

    return render(request, 'private/perfil.html')


@user_passes_test(lambda u: u.is_staff)
def gestion_guias(request, id=None):
    """
    Vista principal para la gestión de guías y usuarios.
    Implementa la lógica MVT para el index-guias.html.
    """
    from .models import Usuario

    all_users = Usuario.objects.all().order_by('-date_joined')
    guias = Usuario.objects.filter(es_guia=True)

    guia_sel = None
    if id:
        guia_sel = get_object_or_404(Usuario, id=id)

    context = {
        'fecha': timezone.now().strftime('%d %b, %Y'),
        'guias': guias,
        'total_guias': guias.count(),
        'total_guias_activos': guias.filter(is_active=True).count(),
        'guias_asignados': 0,
        'total_guias_inactivos': guias.filter(is_active=False).count(),
        'all_users': all_users,
        'total_users': all_users.count(),
        'guia_sel': guia_sel,
    }
    return render(request, 'admin/index-guias.html', context)


@user_passes_test(lambda u: u.is_staff)
def asignar_rol_guia(request, user_id):
    """Toggle para asignar o quitar el rol de guía a un usuario."""
    if request.method == 'POST':
        user_obj = get_object_or_404(Usuario, id=user_id)
        user_obj.es_guia = not user_obj.es_guia
        user_obj.save()
        accion = "asignado como" if user_obj.es_guia else "removido de"
        messages.success(request, f"Usuario {user_obj.username} {accion} guía.")
    return redirect('gestion_guias')


@user_passes_test(lambda u: u.is_staff)
def guias_baja_reactivar(request, id, estado):
    """Cambia el estado de activación de un guía."""
    if request.method == 'POST':
        guia = get_object_or_404(Usuario, id=id)
        guia.is_active = (estado == 'activar')
        guia.save()
        msg = "reactivado" if guia.is_active else "dado de baja"
        messages.info(request, f"Guía {guia.first_name} {msg} exitosamente.")
    return redirect('gestion_guias')


@user_passes_test(lambda u: u.is_staff)
def guias_guardar(request):
    """Lógica para crear o editar un guía desde el modal."""
    if request.method == 'POST':
        # Aquí se implementaría la lógica de guardado/update
        messages.success(request, "Datos del guía guardados correctamente.")
    return redirect('gestion_guias')