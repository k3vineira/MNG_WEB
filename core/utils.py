from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, time

def plantilla_reserva_html(nombre_cliente, paquete, fecha=None, adultos=1, menores=0, punto_encuentro=None, hora_encuentro=None, estado='pendiente', reserva_id='', monto_total='0.00'):
    if isinstance(hora_encuentro, str):
        try:
            hora_encuentro = datetime.strptime(hora_encuentro, '%H:%M').time()
        except ValueError:
            try:
                hora_encuentro = datetime.strptime(hora_encuentro, '%H:%M:%S').time()
            except ValueError:
                hora_encuentro = time(0, 0)

    if not hora_encuentro:
        hora_encuentro = time(0, 0)

    hora_formateada = hora_encuentro.strftime('%H:%M')

    # Configuración de colores y textos por estado de reserva
    if estado == 'confirmada':
        color_tag = "#1E4620"
        bg_caja_estado = "#f4f8f5"
        texto_estado = "Reserva Confirmada"
        bloque_mensaje_estado = "¡Felicidades! Tu pago ha sido verificado con éxito. Tu lugar está completamente asegurado para vivir esta aventura."
    elif estado == 'cancelada':
        color_tag = "#dc3545"
        bg_caja_estado = "#fff5f5"
        texto_estado = "Reserva Cancelada"
        bloque_mensaje_estado = "Te confirmamos que la reserva ha sido dada de baja en nuestro sistema según lo solicitado."
    else:
        color_tag = "#2E6F40"
        bg_caja_estado = "#fafdfb"
        texto_estado = "Reserva Pendiente"
        bloque_mensaje_estado = "Nuestro equipo verificará el comprobante de pago y se pondrá en contacto contigo en breve para confirmar tu reserva. ¡Gracias por elegirnos!"

    bloque_detalles = ""
    if fecha:
        bloque_detalles = f"""
        <tr style="border-bottom: 1px solid #edf2f0;">
            <td style="padding: 12px 0; color: #718096;">Fecha de Salida</td>
            <td style="padding: 12px 0; text-align: right; color: #1a202c;">{fecha}</td>
        </tr>
        """
        if punto_encuentro:
            bloque_detalles += f"""
            <tr style="border-bottom: 1px solid #edf2f0;">
                <td style="padding: 12px 0; color: #718096;">Punto de encuentro</td>
                <td style="padding: 12px 0; text-align: right; color: #1a202c;">{punto_encuentro}</td>
            </tr>
            <tr style="border-bottom: 1px solid #edf2f0;">
                <td style="padding: 12px 0; color: #718096;">Hora de encuentro</td>
                <td style="padding: 12px 0; text-align: right; color: #1a202c;">{hora_formateada}</td>
            </tr>
            """
        bloque_detalles += f"""
        <tr>
            <td style="padding: 12px 0; color: #718096;">Acompañantes</td>
            <td style="padding: 12px 0; text-align: right; color: #1a202c; font-weight: 500;">
                {adultos} Adultos {f'• {menores} Menores' if int(menores) > 0 else ''}
            </td>
        </tr>
        """
    else:
        bloque_detalles = f"""
        <tr>
            <td style="padding: 12px 0; color: #718096;">Monto Total</td>
            <td style="padding: 12px 0; text-align: right; font-weight: 600; color: #1a202c; font-size: 16px;">${monto_total}</td>
        </tr>
        """

    reserva_num_texto = f" #{reserva_id}" if reserva_id else ""

    return f"""
    <html>
    <body style="font-family: 'Segoe UI', Helvetica, Arial, sans-serif; background-color: #f4f7f5; margin: 0; padding: 40px 15px;">
        <div style="max-width: 560px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 8px 24px rgba(30, 70, 32, 0.06);">
            <div style="background-color: #1E4620; text-align: center; padding: 40px 20px 35px 20px;">
                <div style="display: inline-block; background-color: #ffffff; color: #1E4620; width: 46px; height: 46px; line-height: 46px; border-radius: 50%; font-size: 24px; font-weight: bold; font-family: 'Georgia', serif; margin-bottom: 12px; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);">M</div>
                <div style="font-size: 20px; font-weight: 700; color: #ffffff; letter-spacing: 2px; margin-bottom: 6px;">MONAGUA</div>
                <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 2px; color: #a3c7a6; font-weight: bold;">Actualización de Reserva</div>
            </div>
            <div style="padding: 40px; color: #2d3748; line-height: 1.7;">
                <h2 style="font-size: 24px; color: #1E4620; margin-top: 0; font-weight: 600; text-align: center;">¡Notificación de tu Reserva, {nombre_cliente}!</h2>
                <p style="font-size: 15px; color: #4a5568; text-align: center; margin-bottom: 30px;">Se ha registrado una actualización en el estado de tu experiencia.</p>
                <div style="background-color: {bg_caja_estado}; border: 1px solid {color_tag}40; border-radius: 12px; padding: 25px; margin-bottom: 30px;">
                    <div style="text-align: center; margin-bottom: 20px;">
                        <span style="font-size: 12px; font-weight: bold; color: #ffffff; background-color: {color_tag}; padding: 4px 14px; border-radius: 20px; text-transform: uppercase; letter-spacing: 0.5px;">{texto_estado}</span>
                    </div>
                    <table style="width: 100%; border-collapse: collapse; font-size: 15px;">
                        <tr style="border-bottom: 1px solid #edf2f0;">
                            <td style="padding: 12px 0; color: #718096;">Destino / Paquete</td>
                            <td style="padding: 12px 0; text-align: right; font-weight: 600; color: #1a202c;">{paquete}</td>
                            
                        </tr>
                        {bloque_detalles}
                    </table>
                </div>
                <table style="width: 100%; background-color: {bg_caja_estado}; border-radius: 8px; border: 1px dashed {color_tag}30;">
                    <tr>
                        <td style="padding: 15px; font-size: 13px; color: #2d3748; text-align: center; font-weight: 500;">
                            <strong>Nota:</strong> {bloque_mensaje_estado}
                        </td>
                    </tr>
                </table>
            </div>
            <div style="background-color: #fafdfb; text-align: center; padding: 30px 20px; border-top: 1px solid #edf2f0;">
                <p style="margin: 0; font-size: 13px; color: #718096; font-weight: 600;">Monagua Experiencias</p>
                <p style="margin: 5px 0 0 0; font-size: 11px; color: #a0aec0;">Estás recibiendo este correo porque realizaste una solicitud en nuestro sitio web.</p>
                <p style="margin: 15px 0 0 0; font-size: 12px; color: #1E4620; font-weight: bold;">© 2026</p>
            </div>
        </div>
    </body>
    </html>
    """

def plantilla_cancelacion_html(nombre_cliente, paquete, estado, penalidad="0.00"):
    if estado in ['aceptada', 'confirmada']:
        color_tag = "#dc3545"  # Rojo por cancelación aprobada
        bg_caja_estado = "#fff5f5"
        texto_estado = "Solicitud Aceptada"
        mensaje_cuerpo = f'La solicitud de cancelación de tu viaje fue procesada con éxito. Ten en cuenta que se aplicará una penalidad de <strong style="color: #dc3545; font-size: 17px;">${penalidad}</strong> conforme a las políticas del servicio.'
    elif estado in ['rechazada', 'cancelada']:
        color_tag = "#1E4620"
        bg_caja_estado = "#f4f8f5"
        texto_estado = "Solicitud Rechazada"
        mensaje_cuerpo = "Tu solicitud de cancelación ha sido revisada y <strong>no ha sido aprobada</strong>. Esto significa que tu itinerario sigue en pie y <strong>tu reserva continúa completamente activa</strong>. ¡Te esperamos!"
    else:
        color_tag = "#2E6F40"
        bg_caja_estado = "#fafdfb"
        texto_estado = "En Revisión / Recibida"
        mensaje_cuerpo = "Hemos recibido tu solicitud de cancelación. Nuestro equipo está analizando los detalles de tu caso bajo las políticas vigentes. Te enviaremos una notificación definitiva lo antes posible."

    return f"""
    <html>
    <body style="font-family: 'Segoe UI', Helvetica, Arial, sans-serif; background-color: #f4f7f5; margin: 0; padding: 40px 15px;">
        <div style="max-width: 560px; margin: 0 auto; background-color: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 8px 24px rgba(30, 70, 32, 0.06);">
            <div style="background-color: #1E4620; text-align: center; padding: 40px 20px 35px 20px;">
                <div style="display: inline-block; background-color: #ffffff; color: #1E4620; width: 46px; height: 46px; line-height: 46px; border-radius: 50%; font-size: 24px; font-weight: bold; font-family: 'Georgia', serif; margin-bottom: 12px; box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);">M</div>
                <div style="font-size: 20px; font-weight: 700; color: #ffffff; letter-spacing: 2px; margin-bottom: 6px;">MONAGUA</div>
                <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 2px; color: #a3c7a6; font-weight: bold;">Actualización de Solicitud</div>
            </div>
            <div style="padding: 40px; color: #2d3748; line-height: 1.7;">
                <h2 style="font-size: 24px; color: #1E4620; margin-top: 0; text-align: center; font-weight: 600;">Estado de tu Cancelación</h2>
                <p style="font-size: 15px; color: #4a5568; text-align: center; margin-bottom: 30px;">Hola {nombre_cliente}, hay novedades sobre tu solicitud para el paquete: <strong>{paquete}</strong></p>
                <div style="background-color: {bg_caja_estado}; border: 1px solid {color_tag}40; border-radius: 12px; padding: 25px; margin-bottom: 30px; text-align: center;">
                    <span style="font-size: 11px; font-weight: bold; background-color: {color_tag}; color: #ffffff; padding: 4px 14px; border-radius: 20px; text-transform: uppercase; letter-spacing: 1px;">{texto_estado}</span>
                    <p style="margin: 20px 0 0 0; font-size: 15px; color: #2d3748; line-height: 1.6;">{mensaje_cuerpo}</p>
                </div>
                <p style="font-size: 13px; color: #718096; text-align: center; margin-top: 30px;">Si crees que hay un error o requieres asistencia personalizada, responde a este correo directamente.</p>
            </div>
            <div style="background-color: #fafdfb; text-align: center; padding: 30px 20px; border-top: 1px solid #edf2f0;">
                <p style="margin: 0; font-size: 13px; color: #718096; font-weight: 600;">Monagua Experiencias</p>
                <p style="margin: 5px 0 0 0; font-size: 11px; color: #a0aec0;">Estás recibiendo este correo porque realizaste una solicitud en nuestro sitio web.</p>
                <p style="margin: 15px 0 0 0; font-size: 12px; color: #1E4620; font-weight: bold;">© 2026</p>
            </div>
        </div>
    </body>
    </html>
    """

def enviar_correo_html_monagua(asunto, mensaje_texto, destinatario, html_contenido):
    send_mail(
        asunto,
        mensaje_texto,
        settings.EMAIL_HOST_USER,
        [destinatario],
        fail_silently=False,
        html_message=html_contenido
    )
