from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy, reverse
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.db.models import Count, Q
from django.conf import settings
from django.core.mail import send_mail, EmailMultiAlternatives
from django.http import HttpResponse
from django.template.loader import render_to_string
from App.models import Reserva, Paquete, Tarifa

from App.models import Reserva, Paquete, Tarifa
from App.forms.reserva.forms import ReservaForm
from App.utils import (
    plantilla_reserva_html,
    plantilla_cancelacion_html,
    enviar_correo_html_monagua,
    get_image_base64,
    get_qr_base64,
    generar_factura_pdf_bytes,
    enviar_correo_confirmacion_con_factura,
    crear_notificacion_sistema,
    StaffRequiredMixin,
    solo_turistas_requerido
)

def requiere_administrador(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not (request.user.is_authenticated and (request.user.is_staff or getattr(request.user, 'rol', None) == 1)):
            messages.error(request, "No tienes permisos de administrador.")
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def requiere_autenticacion(view_func):
    return login_required(view_func, login_url='login')


# =========================
# GESTIÓN DE RESERVAS (ADMIN)
# =========================

@method_decorator(requiere_administrador, name='dispatch')
class GestionReservasListView(ListView):
    """Vista administrativa para la gestión, filtrado y monitoreo de reservas."""
    model = Reserva
    template_name = 'admin/reserva/reservas_admin.html'
    context_object_name = 'reservas'

    def get_queryset(self):
        estado_param = self.request.GET.get('estado')

        if estado_param == 'todas':
            queryset = Reserva.objects.all()
        elif estado_param:
            queryset = Reserva.objects.filter(estado_reserva=estado_param)
        else:
            queryset = Reserva.objects.exclude(estado_reserva='cancelada')
            
        return queryset.select_related('usuario', 'paquete').order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Gestión de Reservas'
        
        stats = Reserva.objects.aggregate(
            total=Count('id'),
            pendientes=Count('id', filter=Q(estado_reserva='pendiente')),
            confirmadas=Count('id', filter=Q(estado_reserva='confirmada')),
            canceladas=Count('id', filter=Q(estado_reserva='cancelada'))
        )
        context.update(stats)

        context['stats_list'] = [
            ('Total', stats['total'], 'text-dark'),
            ('Pendientes', stats['pendientes'], 'text-warning'),
            ('Confirmadas', stats['confirmadas'], 'text-success'),
            ('Canceladas', stats['canceladas'], 'text-danger'),
        ]

        context['estado_seleccionado'] = self.request.GET.get('estado', '')
        return context


@method_decorator(requiere_administrador, name='dispatch')
class CrearReservaAdminView(SuccessMessageMixin, CreateView):
    model = Reserva
    form_class = ReservaForm
    template_name = 'admin/reserva/agregar_reserva.html'
    success_url = reverse_lazy('gestion_reservas')
    success_message = "¡La reserva ha sido creada con éxito!"

    def form_valid(self, form):
        adultos = form.cleaned_data.get('numero_adultos', 0)
        menores = form.cleaned_data.get('numero_menores', 0)
        nuevo_estado = form.cleaned_data.get('estado_reserva')
        fecha = form.cleaned_data.get('fecha_inicio')

        if adultos < 1:
            form.add_error('numero_adultos', 'Debe haber al menos 1 adulto en la reserva.')
            return self.form_invalid(form)

        if menores < 0:
            form.add_error('numero_menores', 'El número de menores no puede ser negativo.')
            return self.form_invalid(form)

        if nuevo_estado != 'pendiente':
            form.add_error('estado_reserva', 'Una reserva nueva debe quedar pendiente hasta validar el pago.')
            return self.form_invalid(form)

        if fecha and fecha < date.today():
            form.add_error('fecha_inicio', 'No puedes crear reservas en fechas pasadas.')
            return self.form_invalid(form)

        response = super().form_valid(form)

        if self.object.usuario:
            crear_notificacion_sistema(
                usuario=self.object.usuario,
                reserva=self.object,
                mensaje=f"Se ha creado tu reserva para el paquete '{self.object.paquete.nombre}'",
                tipo="Reserva",
                prioridad="media"
            )

        return response


@method_decorator(requiere_administrador, name='dispatch')
class EditarReservaAdminView(UpdateView):
    model = Reserva
    form_class = ReservaForm
    template_name = 'admin/reserva/editar_reserva.html'
    success_url = reverse_lazy('gestion_reservas')

    def form_valid(self, form):
        nuevo_estado = form.cleaned_data.get('estado_reserva')

        reserva_antigua = self.get_object()

        if nuevo_estado == 'confirmada':
            pago = getattr(reserva_antigua, 'pago', None)
            if not pago or pago.estado_transaccion != 'aprobado':
                form.add_error('estado_reserva', 'No se puede confirmar la reserva sin un pago aprobado.')
                return self.form_invalid(form)

        if nuevo_estado == 'cancelada' and reserva_antigua.estado_cancelacion != 'aprobada':
            form.add_error('estado_reserva', 'La reserva solo puede cancelarse después de aprobar la solicitud de cancelación.')
            return self.form_invalid(form)

        valor_viejo = f"Estado: {reserva_antigua.estado_reserva}, Fecha: {reserva_antigua.fecha_inicio}, Adultos: {reserva_antigua.numero_adultos}, Menores: {reserva_antigua.numero_menores}"

        response = super().form_valid(form)
        reserva = self.object
        nombre_cliente = reserva.usuario.first_name or reserva.usuario.username
        
        valor_nuevo = f"Estado: {reserva.estado_reserva}, Fecha: {reserva.fecha_inicio}, Adultos: {reserva.numero_adultos}, Menores: {reserva.numero_menores}"

        if reserva.estado_reserva in ['confirmada', 'cancelada']:
            if reserva.usuario:
                crear_notificacion_sistema(
                    usuario=reserva.usuario,
                    reserva=reserva,
                    mensaje=f"El estado de tu reserva #{reserva.id} ha sido cambiado de '{reserva_antigua.estado_reserva}' a '{reserva.estado_reserva}'.",
                    tipo="Reserva",
                    prioridad="alta"
                )

            if reserva.estado_reserva == 'confirmada':
                try:
                    enviar_correo_confirmacion_con_factura(reserva, request=self.request)
                except Exception as e:
                    print(f"Error enviando correo de confirmación de reserva (admin): {e}")
            else:
                asunto = f"Tu Reserva #{reserva.id} ha sido {reserva.estado_reserva.upper()} - Monagua"
                mensaje_texto = f"Hola {nombre_cliente}, el estado de tu reserva para {reserva.paquete.nombre} ha cambiado a {reserva.estado_reserva}."
                
                html_contenido = plantilla_reserva_html(
                    nombre_cliente=nombre_cliente,
                    paquete=reserva.paquete.nombre,
                    fecha=str(reserva.fecha_inicio),
                    adultos=reserva.numero_adultos,
                    menores=reserva.numero_menores,
                    estado=reserva.estado_reserva,
                    reserva_id=reserva.id,
                    monto_total=str(reserva.monto_total)
                )
                try:
                    enviar_correo_html_monagua(asunto, mensaje_texto, reserva.usuario.email, html_contenido)
                except Exception as e:
                    print(f"Error enviando correo de actualización de reserva: {e}")
                
        return response

@method_decorator(requiere_administrador, name='dispatch')
class EliminarReservaAdminView(DeleteView):
    model = Reserva
    template_name = 'admin/reserva/eliminar_reserva.html'
    success_url = reverse_lazy('gestion_reservas')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        reserva_id = self.object.id
        valor_viejo = f"ID: {self.object.id}, Cliente: {self.object.usuario}, Paquete: {self.object.paquete.nombre if self.object.paquete else 'N/A'}, Estado: {self.object.estado_reserva}"
        response = super().delete(request, *args, **kwargs)

        if self.object.usuario:
            crear_notificacion_sistema(
                usuario=self.object.usuario,
                reserva=self.object,
                mensaje=f"Tu reserva #{reserva_id} ha sido eliminada del sistema. Detalles previos: {valor_viejo}",
                tipo="Reserva",
                prioridad="alta"
            )
        return response


@login_required(login_url='login')
@solo_turistas_requerido
def mis_reservas_usuario(request):
    reservas = Reserva.objects.filter(
        usuario=request.user
    ).exclude(estado_reserva='cancelada').order_by('-fecha_registro')

    context = {
        'reservas': reservas
    }
    return render(request, 'admin/reserva/mis_reservas.html', context)


@login_required(login_url='login')
@solo_turistas_requerido
def cancelar_reserva_usuario(request, reserva_id=None, pk=None):
    """Procesa la cancelación enviada desde el modal, calcula la penalidad numérica y aplica políticas."""
    
    # 1. Validación de método HTTP
    if request.method != 'POST':
        return redirect('mis_reservas_usuario')

    real_id = reserva_id or pk
    reserva = get_object_or_404(Reserva, id=real_id, usuario=request.user)

    # 2. La solicitud no puede repetirse ni aplicarse a una reserva cancelada
    if reserva.estado_reserva == 'cancelada':
        messages.warning(request, "Esta reserva ya se encuentra cancelada.")
        return redirect('mis_cancelaciones')

    if reserva.estado_cancelacion == 'pendiente':
        messages.warning(request, "Ya tienes una solicitud de cancelación pendiente de revisión.")
        return redirect('mis_reservas_usuario')

    # 3. Control de días desde el registro (máximo 3 días para cancelar)
    fecha_reg = getattr(reserva, 'fecha_registro', None)
    if fecha_reg:
        fecha_reg_date = fecha_reg.date() if hasattr(fecha_reg, 'date') else fecha_reg
        if (date.today() - fecha_reg_date).days > 3:
            messages.error(
                request, 
                "Han pasado más de 3 días desde que realizaste la reserva. Ya no es posible cancelarla."
            )
            return redirect('mis_reservas_usuario')

    # 4. Validar motivo ingresado por el usuario
    motivo = request.POST.get('motivo_cancelacion', '').strip()
    if not motivo:
        messages.error(request, "Debes ingresar un motivo válido para solicitar la cancelación.")
        return redirect('mis_reservas_usuario')

    monto_total = Decimal(reserva.monto_total or 0)
    fecha_tour = getattr(reserva, 'fecha_inicio', None)
    
    penalidad_calculada = Decimal('0.00')
    politica_reembolso = "Sujeto a evaluación administrativa."

    if fecha_tour:
 
        fecha_tour_date = fecha_tour.date() if hasattr(fecha_tour, 'date') else fecha_tour
        dias_para_tour = (fecha_tour_date - date.today()).days

      
        if dias_para_tour >= 15:
            penalidad_calculada = monto_total * Decimal('0.10')
            politica_reembolso = "Favorable (Reembolso del 90% / Penalidad del 10%)."
        elif 5 <= dias_para_tour <= 14:
            penalidad_calculada = monto_total * Decimal('0.50')
            politica_reembolso = "Parcial (Reembolso del 50% / Penalidad del 50%)."
        else:
            penalidad_calculada = monto_total
            politica_reembolso = "Sin reembolso (Menos de 5 días / No-Show)."

   
    reserva.motivo_cancelacion = motivo
    reserva.penalidad = penalidad_calculada
    reserva.estado_cancelacion = 'pendiente'
    reserva.save()


    crear_notificacion_sistema(
        usuario=request.user,
        reserva=reserva,
        mensaje=f"Solicitaste la cancelación de tu reserva #{reserva.id}. Motivo: '{motivo}'. Penalidad estimada: COP ${penalidad_calculada:,.0f}",
        tipo="Reserva",
        prioridad="alta"
    )

    
    try:
        asunto = f"Solicitud de cancelación recibida - Reserva #{reserva.id} | Monagua"
        mensaje = (
            f"Hola {request.user.get_full_name() or request.user.username},\n\n"
            f"Recibimos tu solicitud de cancelación para la reserva #{reserva.id}.\n"
            f"La reserva seguirá en estado '{reserva.estado_reserva}' hasta que el equipo la revise.\n\n"
            f"- Motivo: {motivo}\n"
            f"- Penalidad calculada: COP ${penalidad_calculada:,.0f}\n"
            f"- Política aplicada: {politica_reembolso}\n\n"
            f"Atentamente,\nEquipo Monagua"
        )
        send_mail(asunto, mensaje, None, [request.user.email], fail_silently=True)
    except Exception:
        pass

    messages.success(request, f"La solicitud de cancelación de la reserva #{reserva.id} fue enviada para revisión.")
    return redirect('mis_cancelaciones')

@login_required(login_url='login')
def mis_cancelaciones(request):
    """
    Vista para que el usuario consulte el historial de sus reservas canceladas.
    """
    # Filtra las reservas del usuario autenticado que estén canceladas.
    # Ajusta 'cancelada' o 'CANCELADA' según como guardes el estado en tu base de datos.
    cancelaciones = Reserva.objects.filter(
        usuario=request.user,
        estado_cancelacion__isnull=False
    ).select_related('paquete').order_by('-id')

    context = {
        'cancelaciones': cancelaciones
    }
    return render(request, 'admin/reserva/mis_cancelaciones.html', context)

# =========================
# VISTA PÚBLICA
# =========================

@solo_turistas_requerido
def reservas_view(request):
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
        'admin/reserva/reservas.html',
        context
    )


@login_required(login_url='login')
@solo_turistas_requerido
def carrito_view(request):
    reservas_pendientes = Reserva.objects.filter(usuario=request.user, estado_reserva__in=['pendiente', 'Pendiente']).select_related('paquete').order_by('-id')
    context = {
        'reservas': reservas_pendientes
    }
    return render(request, 'usuario/reserva/carrito.html', context)


@login_required(login_url='login')
@solo_turistas_requerido
def comprobante_reserva_html(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
    context = {
        'reserva': reserva,
    }
    return render(request, 'usuario/reserva/comprobante_reserva.html', context)


@login_required(login_url='login')
@solo_turistas_requerido
def comprobante_multiple(request):
    if request.method != 'POST':
        return redirect('carrito')

    ids = request.POST.getlist('reservas')
    if not ids:
        messages.error(request, 'Debes seleccionar al menos una reserva para continuar.')
        return redirect('carrito')

    try:
        ids_int = [int(i) for i in ids]
    except ValueError:
        messages.error(request, 'Selección de reservas inválida.')
        return redirect('carrito')

    reservas_qs = Reserva.objects.filter(id__in=ids_int, usuario=request.user).select_related('paquete')
    reservas = list(reservas_qs)

    if not reservas:
        messages.error(request, 'No se encontraron reservas asociadas a tu usuario.')
        return redirect('carrito')

    total = sum((r.monto_total or 0) for r in reservas)

    context = {
        'reservas': reservas,
        'total': total,
    }
    return render(request, 'usuario/reserva/comprobante_multiple.html', context)


@login_required
@solo_turistas_requerido
def guardar_reserva(request, paquete_id):
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

        fecha_minima = date.today() + timedelta(days=2)
        if fecha_date < fecha_minima:
            messages.error(
                request, 
                f"No es posible reservar para fechas pasadas ni con menos de 2 días de anticipación. "
                f"La fecha mínima permitida es {fecha_minima.strftime('%d/%m/%Y')}."
            )
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

        # --- VALIDACIONES AGREGADAS ---
        if adultos < 1:
            messages.error(request, "Debes seleccionar al menos 1 adulto para realizar la reserva.")
            return redirect(f"/reservas/reservar/?paquete_id={paquete_id}")

        if menores < 0:
            messages.error(request, "El número de menores no puede ser un valor negativo.")
            return redirect(f"/reservas/reservar/?paquete_id={paquete_id}")

        ya_existe = Reserva.objects.filter(
            usuario=request.user,
            paquete=paquete,
            fecha_inicio=fecha_date
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
            fecha_inicio=fecha_date,
            numero_adultos=adultos,
            numero_menores=menores,
            estado_reserva='pendiente'
        )

        crear_notificacion_sistema(
            usuario=request.user,
            reserva=reserva,
            mensaje=f"Se ha creado tu reserva para el paquete '{paquete.nombre}'",
            tipo="Reserva",
            prioridad="media"
        )

        asunto = "Confirmación de tu reserva en Monagua"
        nombre_cliente = request.user.first_name or request.user.username

        mensaje_texto = f"Hola {nombre_cliente}, hemos recibido tu solicitud de reserva para {paquete.nombre}."

        html_bonito = plantilla_reserva_html(
            nombre_cliente=nombre_cliente,
            paquete=paquete.nombre,
            fecha=reserva.fecha_inicio.strftime('%d/%m/%Y'),  
            adultos=reserva.numero_adultos,
            menores=reserva.numero_menores,
            punto_encuentro="Por definir (Sujeto a confirmación)", 
            hora_encuentro="08:00",
            estado=reserva.estado_reserva,
            reserva_id=reserva.id,
            monto_total=str(reserva.monto_total)
        )
        
        correo_enviado = enviar_correo_html_monagua(
            asunto, mensaje_texto, request.user.email, html_bonito)

        if correo_enviado:
            messages.success(
                request, "¡Tu reserva ha sido creada exitosamente! Se ha enviado una confirmación a tu correo.")
        else:
            messages.success(
                request, "¡Tu reserva ha sido registrada con éxito en el sistema!")
        return redirect('mis_reservas_usuario')

    return redirect('reservas')


@login_required(login_url='login')
def mis_facturas(request):
    mis_confirmadas = Reserva.objects.filter(
        usuario=request.user, 
        estado_reserva='confirmada'
    ).select_related('paquete').order_by('-id')
    
    return render(request, 'usuario/reserva/mis_facturas.html', {
        'reservas': mis_confirmadas
    })


@login_required(login_url='login')
def ver_factura(request, reserva_id):
    from django.urls import reverse
    reserva = get_object_or_404(Reserva.objects.select_related('usuario', 'paquete'), id=reserva_id)
    
    if not request.user.is_staff and getattr(request.user, 'rol', None) not in [1, 'ADMIN'] and reserva.usuario != request.user:
        messages.error(request, "No tienes permiso para acceder a esta factura.")
        return redirect('mis_reservas_usuario')
    
    if reserva.estado_reserva != 'confirmada':
        messages.error(request, "La factura solo está disponible para reservas confirmadas y pagadas.")
        return redirect('mis_reservas_usuario')
        
    pago = getattr(reserva, 'pago', None)
    metodo_pago = (pago.banco_origen or pago.metodo_pago) if pago else "Transferencia Bancaria"
    
    abs_url = request.build_absolute_uri(reverse('ver_factura', args=[reserva.id]))
    qr_base64 = get_qr_base64(abs_url)
    
    logo_base64 = get_image_base64('static/img/logo_monagua.webp')
    
    cliente_nombre = getattr(reserva.usuario, 'nombre_completo', None)
    if not cliente_nombre and reserva.usuario:
        cliente_nombre = reserva.usuario.get_full_name() or reserva.usuario.username
    
    context = {
        'reserva_id': reserva.id,
        'nro_factura': f"FAC-1000{reserva.id}",
        'cliente_nombre': cliente_nombre or 'Cliente',
        'cliente_email': reserva.usuario.email if reserva.usuario else '',
        'fecha_emision': reserva.fecha_registro.strftime('%d/%m/%Y') if hasattr(reserva, 'fecha_registro') and reserva.fecha_registro else (reserva.fecha_inicio.strftime('%d/%m/%Y') if reserva.fecha_inicio else ''),
        'metodo_pago': metodo_pago,
        'paquete_nombre': reserva.paquete.nombre if reserva.paquete else 'Aventura Mongua',
        'subtotal': reserva.monto_total,
        'total': reserva.monto_total,
        'logo_base64': logo_base64,
        'qr_base64': qr_base64,
    }
    return render(request, 'usuario/factura.html', context)


@login_required(login_url='login')
def descargar_factura(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    if not request.user.is_staff and reserva.usuario != request.user:
        messages.error(request, "No tienes permiso para descargar esta factura.")
        return redirect('mis_reservas_usuario')
    
    if reserva.estado_reserva != 'confirmada':
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

@requiere_administrador
def listar_cancelaciones_admin(request):
    """Listado y filtrado de solicitudes de cancelación."""


    cancelaciones = Reserva.objects.filter(
        estado_cancelacion__in=['pendiente', 'aprobada', 'rechazada']
    ).select_related('usuario', 'paquete').order_by('-id')

    estado_seleccionado = request.GET.get('estado', '')


    if estado_seleccionado in ['pendiente', 'aprobada', 'rechazada']:
        if estado_seleccionado == 'aprobada':
            cancelaciones = cancelaciones.filter(estado_cancelacion='aprobada')
        else:
            cancelaciones = cancelaciones.filter(estado_cancelacion__iexact=estado_seleccionado)

 
    stats = Reserva.objects.filter(
        estado_cancelacion__in=['pendiente', 'aprobada', 'rechazada']
    ).aggregate(
        total=Count('id'),
        pendientes=Count('id', filter=Q(estado_cancelacion__iexact='pendiente')),
        aprobadas=Count('id', filter=Q(estado_cancelacion__iexact='aprobada')),
        rechazadas=Count('id', filter=Q(estado_cancelacion__iexact='rechazada'))
    )

    stats_list = [
        ('Total', stats['total'], 'text-dark'),
        ('Pendientes', stats['pendientes'], 'text-warning'),
        ('Aprobadas', stats['aprobadas'], 'text-success'),
        ('Rechazadas', stats['rechazadas'], 'text-danger'),
    ]

    context = {
        'cancelaciones': cancelaciones,
        'stats_list': stats_list,
        'estado_seleccionado': estado_seleccionado,
    }

    return render(request, 'admin/reserva/cancelaciones_admin.html', context)

@requiere_administrador
def editar_cancelacion_admin(request, reserva_id):
    """
    Vista para que el administrador revise la cancelación de una Reserva,
    ajuste la penalidad y modifique el estado.
    """

    reserva = get_object_or_404(Reserva, id=reserva_id)

    if request.method == 'POST':
        estado = request.POST.get('estado_cancelacion')
        if estado not in {'pendiente', 'aprobada', 'rechazada'}:
            messages.error(request, "El estado de cancelación no es válido.")
            return redirect('editar_cancelacion_admin', reserva_id=reserva.id)

        estado_anterior = reserva.estado_cancelacion
        reserva.estado_cancelacion = estado
        if estado == 'aprobada':
            reserva.estado_reserva = 'cancelada'
        elif estado == 'rechazada' and reserva.estado_reserva == 'cancelada':
            reserva.estado_reserva = 'confirmada'

        reserva.save()

        if reserva.usuario and estado_anterior != estado:
            crear_notificacion_sistema(
                usuario=reserva.usuario,
                reserva=reserva,
                mensaje=f"La solicitud de cancelación de tu reserva #{reserva.id} fue marcada como '{estado}'.",
                tipo="Reserva",
                prioridad="alta"
            )

        messages.success(request, f"La reserva #{reserva.id} ha sido actualizada.")
        return redirect('listar_cancelaciones')

    return render(request, 'admin/reserva/editar_cancelacion_admin.html', {
        'reserva': reserva
    })
