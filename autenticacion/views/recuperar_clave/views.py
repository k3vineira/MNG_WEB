import random
import time
import logging
from django.shortcuts import render, redirect
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator

from App.models import Usuario
from App.utils import crear_notificacion_sistema
from autenticacion.forms import RecuperacionPersonalizadaForm, RestablecerClaveForm

logger = logging.getLogger(__name__)


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
                    getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@monagua.com'),
                    [email],
                    html_message=html_mensaje,
                    fail_silently=True,
                )
                messages.info(request, f"Hemos enviado un código OTP a {email}.")
                return redirect('verificar_otp_clave')
            except Exception as e:
                logger.warning(f"Aviso de correo recuperación: {e}")
                messages.info(request, f"Por favor verifica tu código OTP enviado a {email}.")
                return redirect('verificar_otp_clave')
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
                logger.error(f"Error enviando correo con el enlace: {e}")
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
