from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import render
from .models import Reserva, Cancelacion
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from catalogo.models import Paquete
from .forms import CancelacionForm
from decimal import Decimal, InvalidOperation
from django.core.mail import send_mail
from datetime import datetime
from catalogo.models import Tarifa
from django.conf import settings
from django.contrib import messages
from django.db.models import Count, Q
from core.utils import (
    plantilla_reserva_html,
    plantilla_cancelacion_html,
    enviar_correo_html_monagua,
    get_image_base64,
    get_qr_base64,
    generar_factura_pdf_bytes,
    enviar_correo_confirmacion_con_factura
)
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse
from django.template.loader import render_to_string
from notificaciones.models import Notificacion
# =========================
# RESERVAS ADMIN 
# =========================


class ReservaListView(ListView):
    model = Reserva
    template_name = 'admin/reservas/reservas.html'
    context_object_name = 'reservas'

    def get_queryset(self):
        """
        get_queryset.
        
        :return: Respuesta de la función.
        """
        return Reserva.objects.exclude(estado='cancelada').order_by('-id')

    def get_context_data(self, **kwargs):
        """
        get_context_data.
        
        :param kwargs: Descripción del parámetro.
        
        :return: Respuesta de la función.
        """
        context = super().get_context_data(**kwargs)
        stats = Reserva.objects.aggregate(
            total=Count('id'),
            pendientes=Count('id', filter=Q(estado='pendiente')),
            confirmadas=Count('id', filter=Q(estado='confirmada')),
            canceladas=Count('id', filter=Q(estado='cancelada'))
        )
        context.update(stats)

        context['stats_list'] = [
            ('Total', stats['total'], 'text-dark'),
            ('Pendientes', stats['pendientes'], 'text-warning'),
            ('Confirmadas', stats['confirmadas'], 'text-success'),
            ('Canceladas', stats['canceladas'], 'text-danger'),
        ]
        return context


class ReservaCreateView(SuccessMessageMixin, CreateView):
    model = Reserva
    fields = ['usuario', 'paquete', 'fecha', 'numero_adultos', 'numero_menores']
    template_name = 'admin/reservas/agregar_reserva.html'
    success_url = ('listar_reservas')

    success_message = "¡La reserva ha sido creada con éxito!"

    def form_valid(self, form):
        """
        form_valid.
        
        :param form: creación de reserva para un paquete específico.
        
        :return: Redirige a la página de listar reservas del usuario después de crear la reserva.
        """
        form.instance.usuario = self.request.user
        return super().form_valid(form)


class ReservaUpdateView(UpdateView):
    model = Reserva
    fields = ['usuario', 'paquete', 'fecha', 'numero_adultos', 'numero_menores', 'estado']
    template_name = 'admin/reservas/editar_reserva.html'
    success_url = reverse_lazy('listar_reservas')

    def form_valid(self, form):
        """
        form_valid.
        
        :param form: edición de reserva para una reserva específica.
        
        :return: Redirige a la página de listar reservas del usuario después de editar la reserva.
        """
        response = super().form_valid(form)
        reserva = self.object
        nombre_cliente = reserva.usuario.first_name or reserva.usuario.username
        
        if reserva.estado in ['confirmada', 'cancelada']:
            Notificacion.objects.create(
                cliente=reserva.usuario,
                titulo=f"Reserva {reserva.estado.upper()}",
                mensaje=f"Tu reserva #{reserva.id} para el paquete '{reserva.paquete.nombre}' ha sido {reserva.estado}.",
                tipo='reserva'
            )

            if reserva.estado == 'confirmada':
                try:
                    enviar_correo_confirmacion_con_factura(reserva, request=self.request)
                except Exception as e:
                    print(f"Error enviando correo de confirmación de reserva (admin): {e}")
            else:
                asunto = f"Tu Reserva #{reserva.id} ha sido {reserva.estado.upper()} - Monagua"
                mensaje_texto = f"Hola {nombre_cliente}, el estado de tu reserva para {reserva.paquete.nombre} ha cambiado a {reserva.estado}."
                
                html_contenido = plantilla_reserva_html(
                    nombre_cliente=nombre_cliente,
                    paquete=reserva.paquete.nombre,
                    fecha=str(reserva.fecha),
                    adultos=reserva.numero_adultos,
                    menores=reserva.numero_menores,
                    estado=reserva.estado,
                    reserva_id=reserva.id,
                    monto_total=str(reserva.monto_total)
                )
                try:
                    enviar_correo_html_monagua(asunto, mensaje_texto, reserva.usuario.email, html_contenido)
                except Exception as e:
                    print(f"Error enviando correo de actualización de reserva: {e}")
                
        return response

class ReservaDeleteView(DeleteView):
    model = Reserva
    template_name = 'admin/reservas/eliminar_reserva.html'
    success_url = reverse_lazy('listar_reservas')


@login_required(login_url='login')
def mis_reservas_usuario(request):
    """
    mis_reservas_usuario.
    
    :param request: las reservas del usuario autenticado y permite ver el historial de reservas.
    
    :return: las reservas del usuario y redirige a la página de mis reservas del usuario.
    """
    mis_reservas = Reserva.objects.filter(usuario=request.user)\
        .select_related('paquete')\
        .prefetch_related('comprobantes', 'cancelaciones')\
        .order_by('-id')

    context = {
        'reservas': mis_reservas
    }
    return render(request, 'usuario/mis_reservas.html', context)


def enviar_correo_monagua(asunto, mensaje, destinatario):
    send_mail(
        asunto,
        mensaje,
        settings.EMAIL_HOST_USER,
        [destinatario],
        fail_silently=False,
    )

# =========================
# CANCELACIONES
# =========================


class CancelacionListView(ListView):
    model = Cancelacion
    template_name = 'admin/cancelaciones/cancelaciones_admin.html'
    context_object_name = 'cancelaciones'

    def get_context_data(self, **kwargs):
        """
        get_context_data.
        
        :param kwargs: Descripción del parámetro.
        
        :return: Respuesta de la función.
        """
        context = super().get_context_data(**kwargs)
        stats = Cancelacion.objects.aggregate(
            total=Count('id'),
            revisando=Count('id', filter=Q(
                estado__in=['pendiente', 'revision'])),
            aceptadas=Count('id', filter=Q(
                estado__in=['confirmada', 'aceptada'])),
            rechazadas=Count('id', filter=Q(
                estado__in=['cancelada', 'rechazada']))
        )
        context['stats_list'] = [
            ('Total', stats['total'], 'text-dark'),
            ('En Revisión', stats['revisando'], 'text-warning'),
            ('Aceptadas', stats['aceptadas'], 'text-success'),
            ('Rechazadas', stats['rechazadas'], 'text-danger'),
        ]
        return context


class CancelacionCreateView(CreateView):
    model = Cancelacion
    fields = ['motivo']
    template_name = 'usuario/cancelaciones/crear_cancelacion.html'
    success_url = reverse_lazy('mis_cancelaciones_usuario')

    def form_valid(self, form):
        """
        form_valid.
        
        :param form: creación de cancelación para una reserva específica.
        
        :return: Redirige a la página de mis cancelaciones del usuario después de crear la cancelación.
        """
        reserva_id = self.request.GET.get('reserva_id')
        if not reserva_id:
            messages.error(self.request, 'No se encontró la reserva para la cancelación.')
            return redirect('mis_cancelaciones_usuario')

        reserva = get_object_or_404(Reserva, id=reserva_id, usuario=self.request.user)

        if reserva.estado == 'cancelada':
            messages.warning(self.request, 'Esta reserva ya está cancelada.')
            return redirect('mis_cancelaciones_usuario')

        if Cancelacion.objects.filter(reserva=reserva, estado__in=['pendiente', 'revision', 'aceptada']).exists():
            messages.warning(self.request, 'Ya existe una solicitud de cancelación activa para esta reserva.')
            return redirect('mis_reservas_usuario')

        form.instance.reserva = reserva
        form.instance.usuario = self.request.user
        form.instance.estado = 'pendiente'  
       
        response = super().form_valid(form)
        
    
        nombre_cliente = self.request.user.first_name or self.request.user.username
        asunto = f"Solicitud de cancelación Recibida - Reserva #{reserva.id}"
        mensaje_texto = f"Hola {nombre_cliente}, hemos recibido tu solicitud de cancelación para el paquete {reserva.paquete.nombre}."
        
        html_cancelacion = plantilla_cancelacion_html(
            nombre_cliente=nombre_cliente,
            paquete=reserva.paquete.nombre,
            estado='pendiente',  
            penalidad="0.00"
        )
        
        try:
            enviar_correo_html_monagua(
                asunto,
                mensaje_texto,
                self.request.user.email,
                html_cancelacion
            )
            messages.success(self.request, 'Tu solicitud de cancelación ha sido enviada y se te ha notificado por correo.')
        except Exception as e:
            print(f"Error al enviar el correo inicial de cancelación: {e}")
            messages.success(self.request, 'Tu solicitud fue radicada pero hubo un inconveniente al enviar la notificación por correo.')

        return response
    
class CancelacionUpdateView(UpdateView):
    model = Cancelacion
    fields = ['estado', 'penalidad']
    template_name = 'admin/cancelaciones/editar_cancelacion.html'
    success_url = reverse_lazy('administrar_cancelaciones')
    

class CancelacionDeleteView(DeleteView):
    model = Cancelacion
    template_name = 'admin/cancelaciones/eliminar_cancelacion.html'
    success_url = reverse_lazy('administrar_cancelaciones')


@login_required(login_url='login')
def mis_cancelaciones_usuario(request):
    """
    mis_cancelaciones_usuario.
    
    :param request: las cancelaciones del usuario autenticado y permite ver el historial de cancelaciones.
    
    :return: las cancelaciones del usuario y redirige a la página de mis cancelaciones del usuario.
    """
    mis_cancelaciones = Cancelacion.objects.filter(reserva__usuario=request.user)\
        .select_related('reserva__paquete')\
        .prefetch_related('reserva__comprobantes')\
        .order_by('-id')

    context = {
        'cancelaciones': mis_cancelaciones
    }
    return render(request, 'usuario/cancelaciones/mis_cancelaciones.html', context)
def administrar_cancelaciones(request):
    """
    administrar_cancelaciones.
    
    :param request: administracion de cancelaciones para el usuario autenticado y permite actualizar el estado y la penalidad de las cancelaciones.
    
    :return: administrar cancelaciones y redirige a la página de administración de cancelaciones del usuario.   
    """
    if request.method == 'POST':
        cancelacion_id = request.POST.get('cancelacion_id')
        cancelacion = get_object_or_404(Cancelacion, id=cancelacion_id)

        cancelacion.estado = request.POST.get('estado')

        penalidad_raw = request.POST.get('penalidad', '0').strip()
        try:
            cancelacion.penalidad = Decimal(penalidad_raw) if penalidad_raw else Decimal('0.00')
        except (InvalidOperation, ValueError):
            cancelacion.penalidad = Decimal('0.00')

        cancelacion.save()

        if cancelacion.estado == 'aceptada':
            cancelacion.reserva.estado = 'cancelada'
        elif cancelacion.estado == 'rechazada':
            cancelacion.reserva.estado = 'confirmada'
        
        cancelacion.reserva.save()

        Notificacion.objects.create(
            cliente=cancelacion.reserva.usuario,
            titulo=f"Cancelación {cancelacion.estado.upper()}",
            mensaje=f"Tu solicitud de cancelación para la reserva #{cancelacion.reserva.id} ha sido {cancelacion.estado}.",
            tipo='reserva'
        )

        nombre_cliente = cancelacion.reserva.usuario.first_name or cancelacion.reserva.usuario.username
        penalidad_str = str(cancelacion.penalidad)

        if cancelacion.estado == 'aceptada':
            asunto = f"Solicitud ACEPTADA para tu Reserva #{cancelacion.reserva.id} - Monagua"
            mensaje_texto = f"Hola {nombre_cliente}, tu solicitud de cancelación para {cancelacion.reserva.paquete.nombre} ha sido aceptada."
        elif cancelacion.estado == 'rechazada':
            asunto = f"Solicitud RECHAZADA para tu Reserva #{cancelacion.reserva.id} - Monagua"
            mensaje_texto = f"Hola {nombre_cliente}, tu solicitud de cancelación para {cancelacion.reserva.paquete.nombre} ha sido rechazada."
        else:
            asunto = f"Actualización de tu Cancelación #{cancelacion.reserva.id} - Monagua"
            mensaje_texto = f"Hola {nombre_cliente}, tu solicitud de cancelación para {cancelacion.reserva.paquete.nombre} cambió de estado."

        try:
            html_cancelacion = plantilla_cancelacion_html(
                nombre_cliente=nombre_cliente,
                paquete=cancelacion.reserva.paquete.nombre,
                estado=cancelacion.estado,
                penalidad=penalidad_str
            )

            enviar_correo_html_monagua(
                asunto,
                mensaje_texto,
                cancelacion.reserva.usuario.email,
                html_cancelacion
            )
        except Exception as e:
            print(f"Error al enviar el correo de resolución de cancelación: {e}")

        return redirect('administrar_cancelaciones')
    

    stats = Cancelacion.objects.aggregate(
        total=Count('id'),
        revisando=Count('id', filter=Q(estado__in=['pendiente', 'revision'])),
        aceptadas=Count('id', filter=Q(estado__in=['confirmada', 'aceptada'])),
        rechazadas=Count('id', filter=Q(estado__in=['cancelada', 'rechazada']))
    )

    stats_list = [
        ('Total', stats['total'], 'text-dark'),
        ('Aceptadas', stats['aceptadas'], 'text-success'),
        ('Rechazadas', stats['rechazadas'], 'text-danger'),
    ]

    cancelaciones_raw = Cancelacion.objects.all().order_by('-id')

    for c in cancelaciones_raw:
        try:
            Decimal(str(c.penalidad))
        except (InvalidOperation, ValueError, TypeError):
            c.penalidad = Decimal('0.00')
            
    context = {
        'cancelaciones': cancelaciones_raw,
        'stats_list': stats_list
    }
    return render(request, 'admin/cancelaciones/cancelaciones_admin.html', context)
 

# VISTA PÚBLICA
# =========================


def reservas_view(request):
    """
    reservas_view.
    
    :param request: reservas para el usuario autenticado y permite seleccionar un paquete para reservar.
    
    :return: reservas y redirige a la página de mis reservas del usuario.
    """
    paquetes = Paquete.objects.all()
    paquete_id = request.GET.get('paquete_id')
    paquete = None
    if paquete_id:
        paquete = get_object_or_404(Paquete, id=paquete_id)

    context = {
        'paquetes': paquetes,
        'paquete': paquete
    }

    return render(
        request,
        'usuario/reservas.html',
        context
    )


@login_required(login_url='login')
def carrito_view(request):
    """Muestra las reservas pendientes del usuario en formato carrito y permite generar comprobante imprimible."""
    reservas_pendientes = Reserva.objects.filter(usuario=request.user, estado__in=['pendiente', 'Pendiente']).select_related('paquete').order_by('-id')
    context = {
        'reservas': reservas_pendientes
    }
    return render(request, 'usuario/carrito.html', context)


@login_required(login_url='login')
def comprobante_reserva_html(request, reserva_id):
    """
    comprobante_reserva_html.
    
    :param request: comprobante de reserva en formato HTML para una reserva específica.
    
    :param reserva_id: comprobante de reserva para la reserva con el ID especificado.
    
    :return: comprobante de reserva en HTML que el usuario puede imprimir o guardar como PDF.
    """
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
    # Render HTML comprobante (Bootstrap) que el usuario puede imprimir/guardar como PDF
    context = {
        'reserva': reserva,
    }
    return render(request, 'usuario/comprobante_reserva.html', context)


@login_required(login_url='login')
def comprobante_multiple(request):
    """Genera un comprobante combinado para varias reservas seleccionadas por el usuario."""
    if request.method != 'POST':
        return redirect('carrito')

    ids = request.POST.getlist('reservas')
    if not ids:
        return redirect('carrito')

    # Convertir a enteros y filtrar reservas válidas del usuario
    try:
        ids_int = [int(i) for i in ids]
    except ValueError:
        return redirect('carrito')

    reservas_qs = Reserva.objects.filter(id__in=ids_int, usuario=request.user).select_related('paquete')
    reservas = list(reservas_qs)

    if not reservas:
        return redirect('carrito')

    total = sum((r.monto_total or 0) for r in reservas)

    context = {
        'reservas': reservas,
        'total': total,
    }
    return render(request, 'usuario/comprobante_multiple.html', context)


# =========================
# VISTA PÚBLICA
# =========================

@login_required
def guardar_reserva(request, paquete_id):
    """
    guardar_reserva.
    
    :param request: guardar reserva para un paquete específico.
    
    :param paquete_id: guarda la reserva para el paquete con el ID especificado.
    
    :return: guardar reserva y redirige a la página de mis reservas del usuario.
    """
    if request.method == 'POST':
        paquete = get_object_or_404(Paquete, id=paquete_id)
        fecha_viaje = request.POST.get('fecha')

        if not fecha_viaje:
            messages.error(request, "Por favor selecciona una fecha válida.")
            return redirect(f"/reservas/reservar/?paquete_id={paquete_id}")

        try:
            fecha_date = datetime.strptime(fecha_viaje, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, "El formato de la fecha no es válido.")
            return redirect(f"/reservas/reservar/?paquete_id={paquete_id}")

        tarifa = Tarifa.objects.filter(
            paquete=paquete,
            temporada__fecha_inicio__lte=fecha_date,
            temporada__fecha_fin__gte=fecha_date
        ).first()

        if not tarifa:
            messages.error(
                request, "No hay tarifas disponibles para esta fecha. Por favor elige otra.")
            return redirect(f"/reservas/reservar/?paquete_id={paquete_id}")

        try:
            adultos = int(request.POST.get('adultos', 1))
            menores = int(request.POST.get('menores', 0))
        except ValueError:
            adultos, menores = 1, 0

        ya_existe = Reserva.objects.filter(
            usuario=request.user,
            paquete=paquete,
            fecha=fecha_date
        ).exists()

        if ya_existe:
            messages.warning(
                request,
                f"Ya tienes una reserva para {paquete.nombre} en la fecha {fecha_viaje}. No se puede crear otra reserva para el mismo paquete y fecha."
            )
            return redirect(f"/reservas/reservar/?paquete_id={paquete_id}")

        reserva = Reserva.objects.create(
            usuario=request.user,
            paquete=paquete,
            fecha=fecha_date,
            numero_adultos=adultos,
            numero_menores=menores,
            estado='pendiente'
        )

        asunto = "Confirmación de tu reserva en Monagua"
        nombre_cliente = request.user.first_name or request.user.username

        mensaje_texto = f"Hola {nombre_cliente}, hemos recibido tu solicitud de reserva para {paquete.nombre}."

        html_bonito = plantilla_reserva_html(
    nombre_cliente=nombre_cliente,
    paquete=paquete.nombre,
    fecha=reserva.fecha.strftime('%d/%m/%Y'),  
    adultos=reserva.numero_adultos,
    menores=reserva.numero_menores,
    punto_encuentro="Por definir (Sujeto a confirmación)", 
    hora_encuentro="08:00",
    estado=reserva.estado,
    reserva_id=reserva.id,
    monto_total=str(reserva.monto_total)
)
        enviar_correo_html_monagua(
            asunto, mensaje_texto, request.user.email, html_bonito)

        messages.success(
            request, "¡Tu reserva ha sido creada y confirmada por correo electrónico!")
        return redirect('mis_reservas_usuario')

    return redirect('reservas')


@login_required(login_url='login')
def mis_facturas(request):
    """Muestra el listado de facturas asociadas a las reservas confirmadas del turista."""
    mis_confirmadas = Reserva.objects.filter(
        usuario=request.user, 
        estado='confirmada'
    ).select_related('paquete').order_by('-id')
    
    return render(request, 'usuario/mis_facturas.html', {
        'reservas': mis_confirmadas
    })


# get_image_base64 y get_qr_base64 se trasladaron a core.utils


@login_required(login_url='login')
def ver_factura(request, reserva_id):
    """Muestra la factura detallada de una reserva confirmada en la web."""
    from django.urls import reverse
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    # Permitir si el usuario es staff (admin) o el dueño de la reserva
    if not request.user.is_staff and reserva.usuario != request.user:
        messages.error(request, "No tienes permiso para acceder a esta factura.")
        return redirect('mis_reservas_usuario')
    
    # Solo permitir ver si está confirmada
    if reserva.estado != 'confirmada':
        messages.error(request, "La factura solo está disponible para reservas confirmadas y pagadas.")
        return redirect('mis_reservas_usuario')
        
    # Obtener el comprobante aprobado para esta reserva para extraer el método de pago
    comprobante = reserva.comprobantes.filter(estado='aprobado').first()
    metodo_pago = comprobante.banco_origen if comprobante else "Transferencia Bancaria"
    
    # Generar URL absoluta para el código QR
    abs_url = request.build_absolute_uri(reverse('ver_factura', args=[reserva.id]))
    qr_base64 = get_qr_base64(abs_url)
    
    # Obtener logo en base64
    logo_base64 = get_image_base64('static/img/logo_monagua.webp')
    
    context = {
        'reserva_id': reserva.id,
        'nro_factura': f"FAC-1000{reserva.id}",
        'cliente_nombre': reserva.usuario.nombre_completo,
        'cliente_email': reserva.usuario.email,
        'fecha_emision': reserva.fecha_registro.strftime('%d/%m/%Y') if hasattr(reserva, 'fecha_registro') and reserva.fecha_registro else reserva.fecha.strftime('%d/%m/%Y'),
        'metodo_pago': metodo_pago,
        'paquete_nombre': reserva.paquete.nombre,
        'subtotal': reserva.monto_total,
        'total': reserva.monto_total,
        'logo_base64': logo_base64,
        'qr_base64': qr_base64,
    }
    return render(request, 'private/factura.html', context)


@login_required(login_url='login')
def descargar_factura(request, reserva_id):
    """Genera y descarga en PDF la factura de la reserva confirmada usando xhtml2pdf."""
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    # Permitir si el usuario es staff (admin) o el dueño de la reserva
    if not request.user.is_staff and reserva.usuario != request.user:
        messages.error(request, "No tienes permiso para descargar esta factura.")
        return redirect('mis_reservas_usuario')
    
    if reserva.estado != 'confirmada':
        messages.error(request, "La factura solo se puede descargar para reservas confirmadas.")
        return redirect('mis_reservas_usuario')
        
    password = reserva.usuario.numero_documento
    if password:
        password = str(password).strip()
        
    try:
        pdf_bytes = generar_factura_pdf_bytes(reserva, request=request, password=password)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="factura_FAC-1000{reserva.id}.pdf"'
        return response
    except Exception as e:
        print(f"Error al descargar la factura PDF: {e}")
        return HttpResponse("Error al generar el PDF de la factura.", status=500)

