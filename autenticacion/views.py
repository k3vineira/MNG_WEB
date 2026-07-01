from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
import random

from usuarios.models import Usuario, Cliente
from .forms import RegistroForm, RecuperacionPersonalizadaForm


def recuperar_apodo_view(request):
    """
    Permite al usuario recuperar su apodo (username) verificando
    su correo electrónico y número de documento en la base de datos.
    """
    context = {}

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        numero_documento = request.POST.get('numero_documento', '').strip()

        if email and numero_documento:
            try:
                usuario = Usuario.objects.get(
                    email__iexact=email,
                    numero_documento=numero_documento
                )
                context['apodo_encontrado'] = usuario.username
            except Usuario.DoesNotExist:
                context['error'] = (
                    'No encontramos ninguna cuenta con ese correo y número de documento. '
                    'Verifica que los datos sean correctos.'
                )
        else:
            context['error'] = 'Por favor completa todos los campos.'

    return render(request, 'authentication/recuperar_apodo.html', context)


def password_reset_request_view(request):
    """
    Vista personalizada para iniciar la recuperación de contraseña.
    Valida Apodo, Documento y Correo, genera un OTP y lo envía.
    """
    if request.method == 'POST':
        form = RecuperacionPersonalizadaForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            # Generar OTP de 6 dígitos
            otp = str(random.randint(100000, 999999))
            
            # Guardar en sesión
            request.session['reset_email'] = email
            request.session['reset_otp'] = otp
            
            # Enviar correo
            subject = 'Código de verificación para recuperar contraseña - Monagua'
            html_message = render_to_string('authentication/password_reset_otp_email.html', {'otp': otp})
            plain_message = strip_tags(html_message)
            send_mail(
                subject,
                plain_message,
                'noreply@monagua.com',
                [email],
                html_message=html_message,
                fail_silently=False,
            )
            
            return redirect('password_reset_otp')
    else:
        form = RecuperacionPersonalizadaForm()

    return render(request, 'authentication/recuperar.html', {'form': form})


def password_reset_otp_verify_view(request):
    """
    Verifica el OTP ingresado por el usuario. Si es correcto, genera
    los tokens de Django y redirige a la vista de confirmación.
    """
    if 'reset_email' not in request.session or 'reset_otp' not in request.session:
        messages.error(request, 'Tu sesión ha expirado o no has iniciado una recuperación.')
        return redirect('password_reset')

    if request.method == 'POST':
        otp_ingresado = request.POST.get('otp', '').strip()
        if otp_ingresado == request.session['reset_otp']:
            # OTP correcto, generar token y redirigir
            email = request.session['reset_email']
            usuario = Usuario.objects.get(email__iexact=email)
            
            uid = urlsafe_base64_encode(force_bytes(usuario.pk))
            token = default_token_generator.make_token(usuario)
            
            # Preparar y enviar el correo con el enlace de restablecimiento
            context = {
                'user': usuario,
                'uid': uid,
                'token': token,
                'protocol': 'https' if request.is_secure() else 'http',
                'domain': request.get_host(),
            }
            subject = 'Enlace para restablecer tu contraseña - Monagua'
            html_message = render_to_string('authentication/password_reset_email.html', context)
            plain_message = strip_tags(html_message)
            
            send_mail(
                subject,
                plain_message,
                'noreply@monagua.com',
                [email],
                html_message=html_message,
                fail_silently=False,
            )
            
            # Limpiar sesión
            del request.session['reset_email']
            del request.session['reset_otp']
            
            return redirect('password_reset_done')
        else:
            messages.error(request, 'El código ingresado es incorrecto. Intenta de nuevo.')

    # Ocultar parcialmente el correo por seguridad (e.g., j***@sena.edu.co)
    email = request.session['reset_email']
    partes = email.split('@')
    email_oculto = f"{partes[0][0]}***@{partes[1]}" if len(partes) == 2 else email

    return render(request, 'authentication/recuperar_otp.html', {'email_oculto': email_oculto})


def registro_view(request):
    """Renderiza y gestiona la plantilla de registro de usuarios."""
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            # Generar OTP de 6 dígitos
            otp = str(random.randint(100000, 999999))
            
            # Guardar en sesión
            request.session['registro_data'] = request.POST.dict()
            request.session['registro_email'] = email
            request.session['registro_otp'] = otp
            
            # Enviar correo
            subject = 'Código de verificación para tu cuenta - Monagua'
            html_message = render_to_string('authentication/registro_otp_email.html', {'otp': otp})
            plain_message = strip_tags(html_message)
            send_mail(
                subject,
                plain_message,
                'noreply@monagua.com',
                [email],
                html_message=html_message,
                fail_silently=False,
            )
            
            return redirect('registro_otp')
        else:
            messages.error(
                request, 'Error en el registro. Verifique los datos.')
    else:
        form = RegistroForm()

    return render(request, 'authentication/registro.html', {
        'titulo': 'Crear Cuenta en Monagua',
        'form': form
    })

def registro_otp_verify_view(request):
    """
    Verifica el OTP ingresado por el usuario en el registro. Si es correcto,
    crea el usuario y lo autentica.
    """
    if 'registro_data' not in request.session or 'registro_otp' not in request.session:
        messages.error(request, 'Tu sesión ha expirado o no has iniciado un registro.')
        return redirect('registro')

    if request.method == 'POST':
        otp_ingresado = request.POST.get('otp', '').strip()
        if otp_ingresado == request.session['registro_otp']:
            # OTP correcto, crear usuario
            form = RegistroForm(request.session['registro_data'])
            if form.is_valid():
                user = form.save(commit=False)
                user.rol = Usuario.Roles.CLIENTE
                user.save()
                registro_data = request.session['registro_data']
                Cliente.objects.create(
                    usuario=user,
                    pais=registro_data.get('pais', ''),
                    ciudad=registro_data.get('ciudad', '')
                )
                login(request, user, backend='autenticacion.backends.EmailOrUsernameModelBackend')
                messages.success(request, 'Registro exitoso. ¡Bienvenido a Monagua!')
                
                # Obtener la URL de redirección si existe
                next_url = registro_data.get('next')
                
                # Limpiar sesión de forma segura
                request.session.pop('registro_data', None)
                request.session.pop('registro_otp', None)
                request.session.pop('registro_email', None)
                
                if next_url:
                    response = redirect(next_url)
                else:
                    response = redirect('inicio')
                response.set_cookie('ha_registrado', 'true', max_age=31536000)  # 1 año
                return response
            else:
                messages.error(request, 'Error al procesar los datos de registro.')
                return redirect('registro')
        else:
            messages.error(request, 'El código ingresado es incorrecto. Intenta de nuevo.')

    email = request.session.get('registro_email', '')
    partes = email.split('@')
    email_oculto = f"{partes[0][0]}***@{partes[1]}" if len(partes) == 2 else email

    return render(request, 'authentication/registro_otp.html', {'email_oculto': email_oculto})


class UsuarioLoginView(LoginView):
    """Vista de inicio de sesión basada en clases para mayor robustez."""
    template_name = 'authentication/login.html'
    redirect_authenticated_user = True
    extra_context = {'titulo': 'Iniciar Sesión — Monagua'}

    def form_valid(self, form):
        """Añade un mensaje de éxito al iniciar sesión correctamente."""
        user = form.get_user()
        messages.success(
            self.request, f'¡Bienvenido nuevamente, {user.first_name or user.username}!')
        return super().form_valid(form)

    def get_success_url(self):
        # 1. Si existe un parámetro '?next=', respetarlo (ej: venía de reservar)
        next_url = self.request.GET.get(
            'next') or self.request.POST.get('next')
        if next_url:
            return next_url

        # 2. Si no, redirigir según el rol del usuario
        if self.request.user.is_staff:
            return reverse_lazy('dashboard')
        return reverse_lazy('index_turista')


class UsuarioLogoutView(LogoutView):
    """Gestiona el cierre de sesión y redirige al inicio."""
    next_page = reverse_lazy('inicio')
    http_method_names = ['get', 'post', 'options']

    def get(self, request, *args, **kwargs):
        """Soporte para cerrar sesión vía GET (evita error 405 en Django 5+)."""
        if request.user.is_authenticated:
            messages.info(request, "Has cerrado sesión correctamente. ¡Vuelve pronto!")
        from django.contrib.auth import logout
        logout(request)
        return redirect(self.next_page)

    def post(self, request, *args, **kwargs):
        """Maneja cerrar sesión vía POST de forma habitual."""
        if request.user.is_authenticated:
            messages.info(request, "Has cerrado sesión correctamente. ¡Vuelve pronto!")
        from django.contrib.auth import logout
        logout(request)
        return redirect(self.next_page)


from django.http import JsonResponse
from django.views.decorators.http import require_GET

@require_GET
def verificar_disponibilidad(request):
    field = request.GET.get('field')
    value = request.GET.get('value', '').strip()
    
    if not field or not value:
        return JsonResponse({'available': True})
        
    exists = False
    message = ""
    
    if field == 'username':
        exists = Usuario.objects.filter(username__iexact=value).exists()
        if exists:
            message = "Este nombre de usuario ya está en uso. Por favor, elige otro."
    elif field == 'email':
        exists = Usuario.objects.filter(email__iexact=value).exists()
        if exists:
            message = "Ya existe un usuario registrado con este correo electrónico."
    elif field == 'numero_documento':
        exists = Usuario.objects.filter(numero_documento=value).exists()
        if exists:
            message = "Ya existe un usuario registrado con este número de documento."
    elif field == 'telefono':
        exists = Usuario.objects.filter(telefono=value).exists()
        if exists:
            message = "Ya existe un usuario registrado con este número de teléfono."
            
    return JsonResponse({
        'available': not exists,
        'message': message
    })
