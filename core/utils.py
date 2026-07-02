from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime, time

def plantilla_reserva_html(nombre_cliente, paquete, fecha=None, adultos=1, menores=0, punto_encuentro=None, hora_encuentro=None, estado='pendiente', reserva_id='', monto_total='0.00'):
    """
    plantilla_reserva_html.
    
    :param nombre_cliente: Descripción del parámetro.
    
    :param paquete: Descripción del parámetro.
    
    :param fecha=None: Descripción del parámetro.
    
    :param adultos=1: Descripción del parámetro.
    
    :param menores=0: Descripción del parámetro.
    
    :param punto_encuentro=None: Descripción del parámetro.
    
    :param hora_encuentro=None: Descripción del parámetro.
    
    :param estado='pendiente': Descripción del parámetro.
    
    :param reserva_id='': Descripción del parámetro.
    
    :param monto_total='0.00': Descripción del parámetro.
    
    :return: Respuesta de la función.
    """
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
    """
    plantilla_cancelacion_html.
    
    :param nombre_cliente: Descripción del parámetro.
    
    :param paquete: Descripción del parámetro.
    
    :param estado: Descripción del parámetro.
    
    :param penalidad="0.00": Descripción del parámetro.
    
    :return: Respuesta de la función.
    """
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
    """
    enviar_correo_html_monagua.
    
    :param asunto: Descripción del parámetro.
    
    :param mensaje_texto: Descripción del parámetro.
    
    :param destinatario: Descripción del parámetro.
    
    :param html_contenido: Descripción del parámetro.
    
    :return: Respuesta de la función.
    """
    send_mail(
        asunto,
        mensaje_texto,
        settings.EMAIL_HOST_USER,
        [destinatario],
        fail_silently=False,
        html_message=html_contenido
    )


def get_image_base64(relative_path):
    """Retorna la representación en base64 de una imagen estática local."""
    import base64
    import os
    from django.conf import settings
    
    file_path = os.path.join(settings.BASE_DIR, relative_path)
    if os.path.exists(file_path):
        with open(file_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            ext = os.path.splitext(file_path)[1].replace('.', '')
            mime = 'image/webp' if ext == 'webp' else ('image/png' if ext == 'png' else 'image/jpeg')
            return f"data:{mime};base64,{encoded_string}"
    return ""


def get_qr_base64(url):
    """Genera un código QR para la URL dada y lo retorna en formato base64."""
    import qrcode
    import io
    import base64

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    encoded_string = base64.b64encode(buffered.getvalue()).decode('utf-8')
    return f"data:image/png;base64,{encoded_string}"


def generar_factura_pdf_bytes(reserva, request=None, password=None):
    """Genera el contenido en bytes del PDF de la factura, opcionalmente protegido por contraseña."""
    import io
    from xhtml2pdf import pisa
    from django.template.loader import render_to_string
    from django.urls import reverse
    from pypdf import PdfReader, PdfWriter
    
    comprobante = reserva.comprobantes.filter(estado='aprobado').first()
    metodo_pago = comprobante.banco_origen if comprobante else "Transferencia Bancaria"
    
    documento_tipo = reserva.usuario.tipo_documento or "Documento"
    documento_num = reserva.usuario.numero_documento or "—"
    
    if request:
        abs_url = request.build_absolute_uri(reverse('ver_factura', args=[reserva.id]))
    else:
        # Fallback si no hay request
        domain = "localhost:8000"
        scheme = "http" if settings.DEBUG else "https"
        abs_url = f"{scheme}://{domain}{reverse('ver_factura', args=[reserva.id])}"
        
    qr_base64 = get_qr_base64(abs_url)
    logo_base64 = get_image_base64('static/img/logo_monagua.webp')
    
    if hasattr(reserva, 'fecha_registro') and reserva.fecha_registro:
        fecha_emision = reserva.fecha_registro.strftime('%d/%m/%Y')
    else:
        fecha_emision = reserva.fecha.strftime('%d/%m/%Y')
        
    context = {
        'nro_factura': f"FAC-1000{reserva.id}",
        'cliente_nombre': reserva.usuario.nombre_completo,
        'cliente_email': reserva.usuario.email,
        'cliente_documento_tipo': documento_tipo,
        'cliente_documento': documento_num,
        'fecha_emision': fecha_emision,
        'metodo_pago': metodo_pago,
        'paquete_nombre': reserva.paquete.nombre,
        'pasajeros_adultos': reserva.numero_adultos,
        'pasajeros_menores': reserva.numero_menores,
        'total': reserva.monto_total,
        'logo_base64': logo_base64,
        'qr_base64': qr_base64,
    }
    
    html_string = render_to_string('private/factura_pdf.html', context)
    pdf_temp = io.BytesIO()
    pisa.pisaDocument(io.BytesIO(html_string.encode("UTF-8")), pdf_temp)
    pdf_bytes = pdf_temp.getvalue()
    
    if password:
        try:
            reader = PdfReader(io.BytesIO(pdf_bytes))
            writer = PdfWriter()
            for page in reader.pages:
                writer.add_page(page)
            writer.encrypt(user_password=password, owner_password=None)
            pdf_encrypted = io.BytesIO()
            writer.write(pdf_encrypted)
            return pdf_encrypted.getvalue()
        except Exception as e:
            print(f"Error encrypting PDF: {e}")
            
    return pdf_bytes


def enviar_correo_confirmacion_con_factura(reserva, request=None):
    """Genera la factura PDF encriptada con el número de documento y envía el correo con diseño OTP."""
    from django.core.mail import EmailMultiAlternatives
    from django.template.loader import render_to_string
    
    password = reserva.usuario.numero_documento
    if password:
        password = str(password).strip()
        
    pdf_bytes = generar_factura_pdf_bytes(reserva, request=request, password=password)
    
    nombre_cliente = reserva.usuario.get_full_name() or reserva.usuario.username
    asunto = f"¡Tu Pago fue Aprobado y tu Reserva #{reserva.id} está Confirmada! - Monagua"
    mensaje_texto = (
        f"Hola {nombre_cliente}, ¡excelentes noticias! Tu comprobante de pago ha sido aprobado con éxito "
        f"y tu aventura está 100% asegurada. Hemos adjuntado tu factura oficial en formato PDF."
    )
    
    context = {
        'nombre_cliente': nombre_cliente,
        'reserva_id': reserva.id,
        'paquete': reserva.paquete.nombre,
        'fecha': reserva.fecha.strftime('%d/%m/%Y') if reserva.fecha else "",
        'adultos': reserva.numero_adultos,
        'menores': reserva.numero_menores,
        'monto_total': str(reserva.monto_total),
        'tiene_password': bool(password),
    }
    
    html_contenido = render_to_string('emails/factura_email.html', context)
    
    email = EmailMultiAlternatives(
        subject=asunto,
        body=mensaje_texto,
        from_email=settings.EMAIL_HOST_USER,
        to=[reserva.usuario.email],
    )
    email.attach_alternative(html_contenido, "text/html")
    
    pdf_filename = f"factura_FAC-1000{reserva.id}.pdf"
    email.attach(pdf_filename, pdf_bytes, "application/pdf")
    
    email.send(fail_silently=False)

