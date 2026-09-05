from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_http_methods
import random
import time

from App.models import Usuario
from App.utils import crear_notificacion_sistema, enviar_correo_html_monagua
from .forms import (
    IniciarSesionForm,
    RegistroForm,
    RecuperacionPersonalizadaForm,
    RestablecerClaveForm
)


# 1. INICIO Y CIERRE DE SESIÓN

def login_vista(request):
    """
    Gestiona el inicio de sesión de usuarios (administradores, clientes, guías).
    Permite autenticarse utilizando correo electrónico o nombre de usuario.
    """
    if request.user.is_authenticated:
        return redirect('tours' if not request.user.is_staff else 'listar_reservas')

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
                            return redirect('listar_reservas')
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


# 2. REGISTRO DE USUARIOS CON OTP

def registro_vista(request):
    """
    Renderiza y procesa el formulario de registro de nuevos clientes.
    Valida duplicados y envía un código OTP de verificación por correo electrónico.
    """
    if request.user.is_authenticated:
        return redirect('tours')

    if request.method == 'POST':
        email_val = request.POST.get('email', '').strip()
        doc_val = request.POST.get('numero_documento', '').strip()
        usr_val = request.POST.get('username', '').strip()
        tel_val = request.POST.get('telefono', '').strip()

        # Validaciones de duplicados tempranas
        if email_val and Usuario.objects.filter(email__iexact=email_val).exists():
            messages.error(request, 'El correo electrónico ya se encuentra registrado.')
            return redirect('registro')

        if doc_val and Usuario.objects.filter(numero_documento=doc_val).exists():
            messages.error(request, 'El número de documento ya se encuentra registrado.')
            return redirect('registro')

        if usr_val and Usuario.objects.filter(username__iexact=usr_val).exists():
            messages.error(request, 'El nombre de usuario ya está en uso.')
            return redirect('registro')

        form = RegistroForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            otp = str(random.randint(100000, 999999))

            # Guardar datos en sesión para creación posterior a la verificación
            request.session['registro_data'] = request.POST.dict()
            request.session['registro_email'] = email
            request.session['registro_otp'] = otp
            request.session['registro_otp_time'] = time.time()

            # Enviar correo con plantilla HTML
            asunto = 'Código de verificación para tu cuenta - Monagua'
            html_mensaje = render_to_string('autenticacion/email_otp_registro.html', {'otp': otp})
            texto_plano = strip_tags(html_mensaje)

            try:
                send_mail(
                    asunto,
                    texto_plano,
                    'noreply@monagua.com',
                    [email],
                    html_message=html_mensaje,
                    fail_silently=False,
                )
                messages.info(request, f"Hemos enviado un código OTP a {email}. Por favor ingrésalo para activar tu cuenta.")
                return redirect('verificar_otp_registro')
            except Exception as e:
                messages.error(request, f"No se pudo enviar el correo de verificación: {e}")
        else:
            messages.error(request, 'Por favor revisa los errores en el formulario.')
    else:
        form = RegistroForm()

    return render(request, 'autenticacion/registro.html', {
        'titulo': 'Crear Cuenta en Monagua',
        'form': form
    })


def verificar_otp_registro_vista(request):
    """
    Verifica el código OTP ingresado por el usuario en el proceso de registro.
    Al ser válido, crea formalmente la cuenta del usuario en la base de datos y lo autentica.
    """
    if 'registro_data' not in request.session or 'registro_otp' not in request.session:
        messages.error(request, 'Tu sesión ha expirado o no has iniciado un registro.')
        return redirect('registro')

    # Expiración a los 10 minutos (600 segundos)
    otp_time = request.session.get('registro_otp_time', 0)
    if time.time() - otp_time > 600:
        request.session.pop('registro_data', None)
        request.session.pop('registro_otp', None)
        request.session.pop('registro_email', None)
        request.session.pop('registro_otp_time', None)
        messages.error(request, 'El código de verificación ha expirado. Por favor inicia tu registro nuevamente.')
        return redirect('registro')

    if request.method == 'POST':
        otp_ingresado = request.POST.get('otp', '').strip()
        if otp_ingresado == request.session['registro_otp']:
            form = RegistroForm(request.session['registro_data'])
            if form.is_valid():
                user = form.save(commit=False)
                user.set_password(form.cleaned_data['password'])
                user.rol = Usuario.Roles.CLIENTE

                # Asegurar persistencia de campos geográficos
                reg_data = request.session.get('registro_data', {})
                if 'pais' in reg_data and reg_data['pais']:
                    user.pais = str(reg_data['pais']).strip()
                if 'departamento' in reg_data and reg_data['departamento']:
                    d_val = str(reg_data['departamento']).strip()
                    user.departamento = int(d_val) if d_val.isdigit() else None
                if 'ciudad' in reg_data and reg_data['ciudad']:
                    c_val = str(reg_data['ciudad']).strip()
                    user.ciudad = int(c_val) if c_val.isdigit() else None

                user.save()

                crear_notificacion_sistema(
                    usuario=user,
                    accion="NUEVO USUARIO REGISTRADO",
                    tabla_afectada="Usuarios",
                    observacion=f"Se ha registrado el nuevo cliente '{user.username}' ({user.email})."
                )

                login(request, user)
                messages.success(request, f'¡Registro exitoso! Bienvenido a la familia Monagua, {user.first_name}.')

                next_url = request.session['registro_data'].get('next')

                # Limpiar datos de sesión temporales
                request.session.pop('registro_data', None)
                request.session.pop('registro_otp', None)
                request.session.pop('registro_email', None)
                request.session.pop('registro_otp_time', None)

                response = redirect(next_url if next_url else 'tours')
                response.set_cookie('ha_registrado', 'true', max_age=31536000)  # 1 año
                return response
            else:
                messages.error(request, 'Ocurrió un error al procesar los datos de registro.')
                return redirect('registro')
        else:
            messages.error(request, 'El código OTP ingresado es incorrecto. Inténtalo nuevamente.')

    email = request.session.get('registro_email', '')
    partes = email.split('@')
    email_oculto = f"{partes[0][0]}***@{partes[1]}" if len(partes) == 2 else email

    return render(request, 'autenticacion/registro_otp.html', {'email_oculto': email_oculto})


# 3. RECUPERACIÓN DE APODO (USERNAME)

def recuperar_apodo_vista(request):
    """
    Permite al usuario recuperar su nombre de usuario (apodo) verificando
    su correo electrónico y/o número de documento en la base de datos.
    """
    context = {}

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        numero_documento = request.POST.get('numero_documento', '').strip()

        if email or numero_documento:
            usuario = None
            try:
                if email and numero_documento:
                    usuario = Usuario.objects.get(
                        email__iexact=email,
                        numero_documento=numero_documento
                    )
                elif email:
                    usuario = Usuario.objects.get(email__iexact=email)
                else:
                    usuario = Usuario.objects.get(numero_documento=numero_documento)

                context['apodo_encontrado'] = usuario.username
            except Usuario.DoesNotExist:
                context['error'] = 'No encontramos ninguna cuenta activa con los datos proporcionados.'
        else:
            context['error'] = 'Por favor ingresa tu correo electrónico o tu número de documento.'

    return render(request, 'autenticacion/recuperar_apodo.html', context)


# 4. RECUPERACIÓN DE CONTRASEÑA CON OTP Y ENLACE SEGURO

def recuperar_clave_vista(request):
    """
    Inicia el flujo de recuperación de contraseña validando apodo, documento y correo.
    Genera un código OTP de 6 dígitos y lo envía por correo electrónico.
    """
    if request.method == 'POST':
        form = RecuperacionPersonalizadaForm(request.POST)
        if form.is_valid():
            usuario = form.cleaned_data['usuario_encontrado']
            email = usuario.email
            otp = str(random.randint(100000, 999999))

            # Guardar en sesión
            request.session['reset_user_id'] = usuario.id
            request.session['reset_email'] = email
            request.session['reset_otp'] = otp
            request.session['reset_otp_time'] = time.time()

            asunto = 'Código de verificación para recuperar contraseña - Monagua'
            html_mensaje = render_to_string('autenticacion/email_otp_recuperar.html', {'otp': otp})
            texto_plano = strip_tags(html_mensaje)

            try:
                send_mail(
                    asunto,
                    texto_plano,
                    'noreply@monagua.com',
                    [email],
                    html_message=html_mensaje,
                    fail_silently=False,
                )
                messages.info(request, f"Hemos enviado un código OTP a {email}.")
                return redirect('verificar_otp_clave')
            except Exception as e:
                messages.error(request, f"Error al enviar el correo: {e}")
        else:
            messages.error(request, 'Los datos no coinciden con ninguna cuenta activa.')
    else:
        form = RecuperacionPersonalizadaForm()

    return render(request, 'autenticacion/recuperar.html', {'form': form})


def verificar_otp_recuperar_vista(request):
    """
    Valida el código OTP ingresado para la recuperación de contraseña.
    Al ser correcto, genera un token criptográfico seguro de un solo uso
    y envía el enlace al correo para establecer la nueva contraseña.
    """
    if 'reset_email' not in request.session or 'reset_otp' not in request.session:
        messages.error(request, 'Tu sesión de recuperación ha expirado o no es válida.')
        return redirect('recuperar_clave')

    # Expiración a los 10 minutos
    otp_time = request.session.get('reset_otp_time', 0)
    if time.time() - otp_time > 600:
        request.session.pop('reset_user_id', None)
        request.session.pop('reset_email', None)
        request.session.pop('reset_otp', None)
        request.session.pop('reset_otp_time', None)
        messages.error(request, 'El código OTP ha expirado. Por favor solicita uno nuevo.')
        return redirect('recuperar_clave')

    if request.method == 'POST':
        otp_ingresado = request.POST.get('otp', '').strip()
        if otp_ingresado == request.session['reset_otp']:
            user_id = request.session['reset_user_id']
            usuario = Usuario.objects.get(id=user_id)

            uid = urlsafe_base64_encode(force_bytes(usuario.pk))
            token = default_token_generator.make_token(usuario)

            contexto_correo = {
                'user': usuario,
                'uid': uid,
                'token': token,
                'protocol': 'https' if request.is_secure() else 'http',
                'domain': request.get_host(),
            }
            asunto = 'Enlace para restablecer tu contraseña - Monagua'
            html_mensaje = render_to_string('autenticacion/email_recuperar_clave.html', contexto_correo)
            texto_plano = strip_tags(html_mensaje)

            try:
                send_mail(
                    asunto,
                    texto_plano,
                    'noreply@monagua.com',
                    [usuario.email],
                    html_message=html_mensaje,
                    fail_silently=False,
                )
            except Exception as e:
                messages.error(request, f"Error enviando correo con el enlace: {e}")

            # Limpiar datos OTP de sesión
            request.session.pop('reset_user_id', None)
            request.session.pop('reset_email', None)
            request.session.pop('reset_otp', None)
            request.session.pop('reset_otp_time', None)

            return redirect('clave_enviada')
        else:
            messages.error(request, 'El código OTP ingresado es incorrecto.')

    email = request.session.get('reset_email', '')
    partes = email.split('@')
    email_oculto = f"{partes[0][0]}***@{partes[1]}" if len(partes) == 2 else email

    return render(request, 'autenticacion/verificar_otp.html', {'email_oculto': email_oculto})


def restablecer_clave_enviado_vista(request):
    """Pantalla informativa que confirma el envío del correo con el enlace de restablecimiento."""
    return render(request, 'autenticacion/recuperar_clave_enviado.html')


def restablecer_clave_confirmar_vista(request, uidb64, token):
    """
    Valida el token de restablecimiento recibido por correo y permite al usuario
    ingresar su nueva contraseña.
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        usuario = Usuario.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Usuario.DoesNotExist):
        usuario = None

    if usuario is not None and default_token_generator.check_token(usuario, token):
        validlink = True
        form = RestablecerClaveForm(request.POST or None)

        if request.method == 'POST' and form.is_valid():
            nueva_clave = form.cleaned_data['new_password1']
            usuario.set_password(nueva_clave)
            usuario.save()

            crear_notificacion_sistema(
                usuario=usuario,
                accion="CAMBIO DE CONTRASEÑA",
                tabla_afectada="Usuarios",
                observacion=f"El usuario '{usuario.username}' restableció su contraseña exitosamente."
            )
            return redirect('clave_guardada')

        return render(request, 'autenticacion/recuperar_clave_form.html', {
            'form': form,
            'validlink': validlink,
            'uidb64': uidb64,
            'token': token,
        })
    else:
        validlink = False
        return render(request, 'autenticacion/recuperar_clave_form.html', {
            'validlink': validlink,
            'form': None
        })


def restablecer_clave_guardar_vista(request):
    """Pantalla informativa de éxito tras haber cambiado la contraseña satisfactoriamente."""
    return render(request, 'autenticacion/recuperar_clave_guardar.html')


# 5. VALIDACIÓN EN TIEMPO REAL (AJAX)

@require_GET
def verificar_campo_ajax(request):
    """
    Verifica en tiempo real si un dato (username, email, numero_documento, telefono)
    ya existe en la base de datos para la validación interactiva del registro.
    """
    campo = request.GET.get('campo', '').strip()
    valor = request.GET.get('valor', '').strip()

    if not campo or not valor:
        return JsonResponse({'error': 'Parámetros inválidos'}, status=400)

    disponible = True
    mensaje = ""

    if campo == 'username':
        exists = Usuario.objects.filter(username__iexact=valor).exists()
        if exists:
            disponible = False
            mensaje = "Este nombre de usuario ya está registrado."

    elif campo == 'email':
        exists = Usuario.objects.filter(email__iexact=valor).exists()
        if exists:
            disponible = False
            mensaje = "Este correo electrónico ya está registrado."

    elif campo == 'numero_documento':
        exists = Usuario.objects.filter(numero_documento=valor).exists()
        if exists:
            disponible = False
            mensaje = "Este número de documento ya está registrado."

    elif campo == 'telefono':
        exists = Usuario.objects.filter(telefono=valor).exists()
        if exists:
            disponible = False
            mensaje = "Este número de teléfono ya está registrado."

    return JsonResponse({
        'disponible': disponible,
        'mensaje': mensaje
    })


# 7. APIS GEOGRÁFICAS LOCALES (DATASET DR5HN)

@require_GET
def api_paises(request):
    """
    Retorna la lista de países disponibles en el dataset local dr5hn.
    """
    from .geografia import get_paises
    paises = get_paises()
    return JsonResponse(paises, safe=False)


@require_GET
def api_departamentos(request, pais_id):
    """
    Retorna los departamentos o estados de un país (por ISO3, ISO2 o ID).
    """
    from .geografia import get_departamentos
    departamentos = get_departamentos(pais_id)
    return JsonResponse(departamentos, safe=False)


@require_GET
def api_ciudades(request, departamento_id):
    """
    Retorna los municipios o ciudades de un departamento dado por su ID.
    """
    from .geografia import get_ciudades
    ciudades = get_ciudades(departamento_id)
    return JsonResponse(ciudades, safe=False)

