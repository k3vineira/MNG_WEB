import random
import time
import logging
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from App.models import Usuario
from App.utils import crear_notificacion_sistema
from autenticacion.forms import RegistroForm

logger = logging.getLogger(__name__)


def registro_vista(request):
    """
    Renderiza y procesa el formulario de registro de nuevos clientes.
    Valida duplicados y envía un código OTP de verificación por correo electrónico.
    """
    if request.user.is_authenticated:
        if request.user.is_staff or getattr(request.user, 'rol', None) == Usuario.Roles.ADMIN:
            return redirect('listar_reservas')
        elif getattr(request.user, 'es_turista', False):
            return redirect('panel_rapido')
        return redirect('panel_rapido')

    if request.method == 'POST':
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
                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', getattr(settings, 'EMAIL_HOST_USER', 'webmonagua@gmail.com'))
                send_mail(
                    asunto,
                    texto_plano,
                    from_email,
                    [email],
                    html_message=html_mensaje,
                    fail_silently=False,
                )
                messages.info(request, "Hemos generado tu código OTP de verificación. Por favor ingrésalo para activar tu cuenta.")
                return redirect('verificar_otp_registro')
            except Exception as e:
                logger.error(f"Error al enviar correo de verificación: {e}")
                messages.error(request, f"No se pudo enviar el correo de verificación a {email}: {e}")
                return redirect('registro')
        else:
            errores_detalles = []
            for field, err_list in form.errors.items():
                err_text = str(err_list[0])
                if field == '__all__':
                    errores_detalles.append(err_text)
                else:
                    field_label = form.fields[field].label if field in form.fields else field
                    errores_detalles.append(f"{field_label}: {err_text}")
            
            error_msg = " | ".join(errores_detalles) if errores_detalles else "Por favor verifica los campos resaltados en el formulario."
            messages.error(request, error_msg)
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

    error_otp = False

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

                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, f'¡Registro exitoso! Bienvenido a la familia Monagua, {user.first_name}.')

                next_url = request.session['registro_data'].get('next')

                # Limpiar datos de sesión temporales
                request.session.pop('registro_data', None)
                request.session.pop('registro_otp', None)
                request.session.pop('registro_email', None)
                request.session.pop('registro_otp_time', None)

                response = redirect(next_url if next_url else 'panel_rapido')
                response.set_cookie('ha_registrado', 'true', max_age=31536000)  # 1 año
                return response
            else:
                errores = " | ".join([f"{f}: {err[0]}" for f, err in form.errors.items()])
                messages.error(request, f'Ocurrió un error al procesar los datos de registro: {errores}')
                return redirect('registro')
        else:
            error_otp = True
            messages.error(request, 'El código OTP ingresado es incorrecto. Inténtalo nuevamente.')

    email = request.session.get('registro_email', '')
    partes = email.split('@')
    email_oculto = f"{partes[0][0]}***@{partes[1]}" if len(partes) == 2 else email

    return render(request, 'autenticacion/registro_otp.html', {
        'email_oculto': email_oculto,
        'error_otp': error_otp
    })


def reenviar_otp_registro_vista(request):
    """
    Genera y reenvía un nuevo código OTP para el registro activo sin perder los datos.
    """
    if 'registro_data' not in request.session or 'registro_email' not in request.session:
        messages.error(request, 'Tu sesión de registro ha expirado. Por favor inicia nuevamente.')
        return redirect('registro')

    email = request.session['registro_email']
    nuevo_otp = str(random.randint(100000, 999999))
    request.session['registro_otp'] = nuevo_otp
    request.session['registro_otp_time'] = time.time()

    asunto = 'Nuevo código de verificación para tu cuenta - Monagua'
    html_mensaje = render_to_string('autenticacion/email_otp_registro.html', {'otp': nuevo_otp})
    texto_plano = strip_tags(html_mensaje)

    try:
        from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', getattr(settings, 'EMAIL_HOST_USER', 'webmonagua@gmail.com'))
        send_mail(
            asunto,
            texto_plano,
            from_email,
            [email],
            html_message=html_mensaje,
            fail_silently=False,
        )
        messages.success(request, f'Se ha generado y enviado un nuevo código OTP a {email}.')
    except Exception as e:
        logger.error(f"Error reenviando OTP de registro: {e}")
        messages.error(request, f"No se pudo reinsertar/enviar el código a {email}: {e}")

    return redirect('verificar_otp_registro')
