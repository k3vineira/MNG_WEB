from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import Cliente
from .forms import RegistroForm


@login_required
def inicio_usuarios(request):
    """
    Punto de entrada tras el login. Redirige a los administradores al dashboard
    y a los turistas a su página de inicio personalizada.
    """
    if request.user.is_staff:
        return redirect('usuarios:dashboard')

    context = {
        'titulo': 'Bienvenido a Monagua',
    }
    return render(request, 'usuarios/index-admin.html', context)


@user_passes_test(lambda u: u.is_staff, login_url='usuarios:inicio')
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
        return redirect('usuarios:inicio')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
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
                
                # Redirigir a 'next' si existe (útil para reservas interrumpidas)
                next_url = request.GET.get('next')
                if next_url:
                    return redirect(next_url)
                return redirect('usuarios:inicio')
    else:
        form = AuthenticationForm()
    return render(request, 'authentication/login.html', {'form': form})


def logout_view(request):
    """
    Cierra la sesión del usuario y redirige a la página de inicio de sesión.
    """
    auth_logout(request)
    messages.info(request, "Has cerrado sesión exitosamente.")
    return redirect('usuarios:login')


def registro_view(request):
    if request.user.is_authenticated:
        return redirect('usuarios:inicio')

    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.es_turista = True  # Asignar rol de turista automáticamente
            user.save()
            
            # Crear el perfil de Cliente asociado
            Cliente.objects.create(usuario=user, telefono=user.telefono)
            
            messages.success(request, "¡Registro exitoso! Tu cuenta ha sido creada. Ahora puedes iniciar sesión.")
            # Redirigir al login en lugar de iniciar sesión automáticamente
            return redirect('usuarios:login')
        else:
            messages.error(request, "Hubo un error en el registro. Por favor, revisa los datos.")
    else:
        form = RegistroForm()

    return render(request, 'authentication/registro.html', {'form': form})


def terminos_view(request):
    return render(
        request,
        'public/terminos.html'
    )

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
            
        return redirect('usuarios:detalles')

    return render(request, 'private/perfil.html')