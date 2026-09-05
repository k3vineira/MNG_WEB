from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import render
from .models import Reserva, Cancelacion
from django.utils.decorators import method_decorator
from core.decoradores import requiere_administrador, requiere_autenticacion
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from catalogo.models import Paquete
from .forms import CancelacionForm , ReservaForm
from datetime import date, timedelta
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
from auditoria.utils import crear_notificacion_sistema


# =========================
# RESERVAS ADMIN 
# =========================

@method_decorator(requiere_administrador, name='dispatch')
class ReservaListView(ListView):
    model = Reserva
    template_name = 'admin/reservas/reservas.html'
    context_object_name = 'reservas'

    def get_queryset(self):
        estado_param = self.request.GET.get('estado')

        if estado_param == 'todas':
            queryset = Reserva.objects.all()
        elif estado_param:
            queryset = Reserva.objects.filter(estado=estado_param)
        else:
            queryset = Reserva.objects.exclude(estado='cancelada')
            
        return queryset.select_related('usuario', 'paquete').order_by('-id')

    def get_context_data(self, **kwargs):
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

        context['estado_seleccionado'] = self.request.GET.get('estado', '')
        return context


from django.http import JsonResponse
import json

@requiere_administrador
def cambiar_estado_reserva(request, reserva_id):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nuevo_estado = data.get('estado')
            
            reserva = get_object_or_404(Reserva, id=reserva_id)
            if nuevo_estado not in dict(Reserva.ESTADO_CHOICES).keys():
                return JsonResponse({'success': False, 'error': 'Estado no válido.'}, status=400)
            
            estado_anterior = reserva.estado
            reserva.estado = nuevo_estado
            reserva.save()
            
            crear_notificacion_sistema(
                usuario=request.user,
                accion=f"RESERVA {nuevo_estado.upper()}",
                tabla_afectada="Reservas",
                observacion=f"La reserva #{reserva.id} para el paquete '{reserva.paquete.nombre}' ha cambiado a {nuevo_estado} de forma rápida.",
                valor_anterior=f"Estado: {estado_anterior}",
                nuevo_valor=f"Estado: {nuevo_estado}"
            )
            
            return JsonResponse({'success': True, 'estado': nuevo_estado, 'mensaje': f'Estado actualizado a {nuevo_estado}'})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    return JsonResponse({'success': False, 'error': 'Método no permitido.'}, status=405)


    
@method_decorator(requiere_administrador, name='dispatch')
class ReservaCreateView(SuccessMessageMixin, CreateView):
    model = Reserva
    form_class = ReservaForm
    template_name = 'admin/reservas/agregar_reserva.html'
    success_url = reverse_lazy('listar_reservas')
    success_message = "¡La reserva ha sido creada con éxito!"

 
    def form_valid(self, form):
        adultos = form.cleaned_data.get('numero_adultos', 0)
        menores = form.cleaned_data.get('numero_menores', 0)
        fecha = form.cleaned_data.get('fecha')

        if adultos < 1:
            form.add_error('numero_adultos', 'Debe haber al menos 1 adulto en la reserva.')
            return self.form_invalid(form)

        if menores < 0:
            form.add_error('numero_menores', 'El número de menores no puede ser negativo.')
            return self.form_invalid(form)

        if fecha and fecha < date.today():
            form.add_error('fecha', 'No puedes crear reservas en fechas pasadas.')
            return self.form_invalid(form)

        response = super().form_valid(form)

        crear_notificacion_sistema(
            usuario=self.request.user,
            accion="NUEVA RESERVA CREADA",
            tabla_afectada="Reservas",
            observacion=f"Se ha registrado manualmente la reserva #{self.object.id} para el paquete '{self.object.paquete.nombre}'.",
            valor_anterior="Ninguno (Registro Nuevo)",
            nuevo_valor=f"Cliente: {self.object.usuario.get_full_name() or self.object.usuario.username}, Fecha: {self.object.fecha}, Adultos: {self.object.numero_adultos}, Menores: {self.object.numero_menores}"
        )

        return response


@method_decorator(requiere_administrador, name='dispatch')
class ReservaUpdateView(UpdateView):
    model = Reserva
    form_class = ReservaForm
    template_name = 'admin/reservas/editar_reserva.html'
    success_url = reverse_lazy('listar_reservas')

    # --- VALIDACIÓN AGREGADA ---
    def form_valid(self, form):
        adultos = form.cleaned_data.get('numero_adultos', 0)
        menores = form.cleaned_data.get('numero_menores', 0)

        if adultos < 1:
            form.add_error('numero_adultos', 'Debe haber al menos 1 adulto en la reserva.')
            return self.form_invalid(form)

        if menores < 0:
            form.add_error('numero_menores', 'El número de menores no puede ser negativo.')
            return self.form_invalid(form)

        reserva_antigua = self.get_object()
        valor_viejo = f"Estado: {reserva_antigua.estado}, Fecha: {reserva_antigua.fecha}, Adultos: {reserva_antigua.numero_adultos}, Menores: {reserva_antigua.numero_menores}"

        response = super().form_valid(form)
        reserva = self.object
        nombre_cliente = reserva.usuario.first_name or reserva.usuario.username
        
        valor_nuevo = f"Estado: {reserva.estado}, Fecha: {reserva.fecha}, Adultos: {reserva.numero_adultos}, Menores: {reserva.numero_menores}"

        if reserva.estado in ['confirmada', 'cancelada']:
            crear_notificacion_sistema(
                usuario=self.request.user,
                accion=f"RESERVA {reserva.estado.upper()}",
                tabla_afectada="Reservas",
                observacion=f"La reserva #{reserva.id} para el paquete '{reserva.paquete.nombre}' ha cambiado a {reserva.estado}.",
                valor_anterior=valor_viejo,
                nuevo_valor=valor_nuevo
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

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        reserva_id = self.object.id
        valor_viejo = f"ID: {self.object.id}, Cliente: {self.object.usuario}, Paquete: {self.object.paquete.nombre}, Estado: {self.object.estado}"

        response = super().delete(request, *args, **kwargs)

        crear_notificacion_sistema(
            usuario=request.user,
            accion="RESERVA ELIMINADA",
            tabla_afectada="Reservas",
            observacion=f"Se ha eliminado del sistema la reserva #{reserva_id}.",
            valor_anterior=valor_viejo,
            nuevo_valor="Registro Eliminado"
        )
        return response


@login_required(login_url='login')
def mis_reservas_usuario(request):
    mis_reservas = Reserva.objects.filter(usuario=request.user)\
        .select_related('paquete')\
        .prefetch_related('cancelaciones')\
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

    def get_queryset(self):
        queryset = super().get_queryset()
        estado_param = self.request.GET.get('estado')

        if estado_param and estado_param != 'todas':
            queryset = queryset.filter(estado=estado_param)
            
        return queryset.order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        stats = Cancelacion.objects.aggregate(
            total=Count('id'),
            pendientes=Count('id', filter=Q(estado='pendiente')),
            aceptadas=Count('id', filter=Q(estado='aceptada')),
            rechazadas=Count('id', filter=Q(estado='rechazada'))
        )
        context.update(stats)
        
        context['stats_list'] = [
            ('Total', stats['total'], 'text-dark'),
            ('En Revisión', stats['pendientes'], 'text-warning'),
            ('Aceptadas', stats['aceptadas'], 'text-success'),
            ('Rechazadas', stats['rechazadas'], 'text-danger'),
        ]

        context['estado_seleccionado'] = self.request.GET.get('estado', '')
        return context


@method_decorator(requiere_autenticacion, name='dispatch')
class CancelacionCreateView(CreateView):
    model = Cancelacion
    form_class = CancelacionForm
    template_name = 'usuario/cancelaciones/crear_cancelacion.html'
    
    def get_success_url(self):
        return reverse_lazy('mis_reservas_usuario')

    # --- VALIDACIONES AGREGADAS ---
    def form_valid(self, form):
        motivo = form.cleaned_data.get('motivo', '').strip()
        if not motivo or len(motivo) < 10:
            messages.error(self.request, 'Por favor ingresa un motivo detallado (mínimo 10 caracteres).')
            return self.form_invalid(form)

        reserva_id = self.request.GET.get('reserva_id')
        if not reserva_id:
            messages.error(self.request, 'No se encontró la reserva para la cancelación.')
            return redirect('mis_reservas_usuario')

        reserva = get_object_or_404(Reserva, id=reserva_id, usuario=self.request.user)

        if reserva.estado.lower() == 'cancelada':
            messages.warning(self.request, 'Esta reserva ya está cancelada.')
            return redirect('mis_reservas_usuario')

        nombre_cliente = self.request.user.first_name or self.request.user.username

        if reserva.estado.lower() == 'pendiente' and reserva.estado_pago == 'sin_pago':
            reserva.estado = 'cancelada'
            reserva.save()

            crear_notificacion_sistema(
                usuario=self.request.user,
                accion="RESERVA DESCARTADA",
                tabla_afectada="Cancelaciones",
                observacion=f"El cliente descartó su reserva pendiente #{reserva.id} directamente sin penalización.",
                valor_anterior=f"Estado Reserva: Pendiente",
                nuevo_valor=f"Estado Reserva: Cancelada"
            )

            asunto = f"Reserva #{reserva.id} Descartada - Monagua"
            mensaje_texto = f"Hola {nombre_cliente}, has cancelado tu reserva pendiente para {reserva.paquete.nombre}. No se aplicaron cargos."
            
            html_cancelacion = plantilla_cancelacion_html(
                nombre_cliente=nombre_cliente,
                paquete=reserva.paquete.nombre,
                estado='cancelada',  
                penalidad="0.00"
            )
            
            try:
                enviar_correo_html_monagua(asunto, mensaje_texto, self.request.user.email, html_cancelacion)
            except Exception as e:
                print(f"Error al enviar correo de reserva descartada: {e}")

            messages.success(self.request, 'Tu reserva pendiente ha sido cancelada exitosamente sin ninguna penalización.')
            return redirect('mis_reservas_usuario')

        if Cancelacion.objects.filter(reserva=reserva, estado__in=['pendiente', 'revision', 'aceptada']).exists():
            messages.warning(self.request, 'Ya existe una solicitud de cancelación activa para esta reserva.')
            return redirect('mis_reservas_usuario')

        form.instance.reserva = reserva
        form.instance.usuario = self.request.user
        form.instance.estado = 'pendiente'  
       
        response = super().form_valid(form)
        
        crear_notificacion_sistema(
            usuario=self.request.user,
            accion="SOLICITUD DE CANCELACIÓN ENVIADA",
            tabla_afectada="Cancelaciones",
            observacion=f"Solicitud de cancelación radica para la reserva #{reserva.id}.",
            valor_anterior="Sin Solicitud",
            nuevo_valor=f"Estado Solicitud: Pendiente, Motivo: {self.object.motivo}"
        )

        asunto = f"Solicitud de cancelación en revisión - Reserva #{reserva.id}"
        mensaje_texto = f"Hola {nombre_cliente}, recibimos tu solicitud. Como ya registraste un pago, un asesor revisará tu caso."
        
        html_cancelacion = plantilla_cancelacion_html(
            nombre_cliente=nombre_cliente,
            paquete=reserva.paquete.nombre,
            estado='pendiente',  
            penalidad="Sujeta a revisión (Pago detectado)"
        )
        
        try:
            enviar_correo_html_monagua(asunto, mensaje_texto, self.request.user.email, html_cancelacion)
            messages.success(self.request, 'Tu solicitud ha sido enviada. Un administrador revisará el comprobante adjunto para procesar la devolución o penalidad.')
        except Exception as e:
            print(f"Error al enviar el correo de cancelación: {e}")
            messages.success(self.request, 'Solicitud radicada. Revisaremos tu comprobante de pago a la brevedad.')

        return response
    
class CancelacionUpdateView(UpdateView):
    model = Cancelacion
    form_class = CancelacionForm
    template_name = 'admin/cancelaciones/editar_cancelacion.html'
    success_url = reverse_lazy('administrar_cancelaciones')

    
    def form_valid(self, form):
        penalidad = form.cleaned_data.get('penalidad')
        if penalidad is not None and penalidad < Decimal('0.00'):
            form.add_error('penalidad', 'La penalidad no puede ser un valor negativo.')
            return self.form_invalid(form)
        return super().form_valid(form)


    def post(self, request, *args, **kwargs):
        cancelacion = self.get_object()
        if cancelacion.estado in ('aceptada', 'rechazada'):
            messages.error(request, 'Esta cancelación ya ha sido procesada y no puede modificarse.')
            return redirect('administrar_cancelaciones')
        return super().post(request, *args, **kwargs)

@method_decorator(requiere_administrador, name='dispatch')
class CancelacionDeleteView(DeleteView):
    model = Cancelacion
    template_name = 'admin/cancelaciones/eliminar_cancelacion.html'
    success_url = reverse_lazy('administrar_cancelaciones')

@login_required(login_url='login')
def mis_cancelaciones_usuario(request):
    mis_cancelaciones = Cancelacion.objects.filter(reserva__usuario=request.user)\
        .select_related('reserva__paquete')\
        .order_by('-id')

    context = {
        'cancelaciones': mis_cancelaciones
    }
    return render(request, 'usuario/cancelaciones/mis_cancelaciones.html', context)


@login_required(login_url='login')
def administrar_cancelaciones(request):
    if not request.user.is_staff:
        messages.error(request, "Acceso denegado. Se requieren permisos de administrador.")
        return redirect('mis_reservas_usuario')

    if request.method == 'POST':
        cancelacion_id = request.POST.get('cancelacion_id')
        cancelacion = get_object_or_404(Cancelacion, id=cancelacion_id)

        estado_anterior = cancelacion.estado
        penalidad_anterior = cancelacion.penalidad

        cancelacion.estado = request.POST.get('estado')

        penalidad_raw = request.POST.get('penalidad', '0').strip()
        try:
            penalidad_val = Decimal(penalidad_raw) if penalidad_raw else Decimal('0.00')
            # --- VALIDACIÓN AGREGADA ---
            if penalidad_val < Decimal('0.00'):
                messages.error(request, 'La penalidad no puede ser un número negativo.')
                return redirect('administrar_cancelaciones')
            cancelacion.penalidad = penalidad_val
        except (InvalidOperation, ValueError):
            cancelacion.penalidad = Decimal('0.00')

        cancelacion.save()

        if cancelacion.estado == 'aceptada':
            cancelacion.reserva.estado = 'cancelada'
        elif cancelacion.estado == 'rechazada':
            cancelacion.reserva.estado = 'confirmada'
        
        cancelacion.reserva.save()

        crear_notificacion_sistema(
            usuario=request.user,
            accion=f"CANCELACIÓN {cancelacion.estado.upper()}",
            tabla_afectada="Cancelaciones",
            observacion=f"La solicitud de cancelación para la reserva #{cancelacion.reserva.id} fue procesada a estado '{cancelacion.estado}'.",
            valor_anterior=f"Estado: {estado_anterior}, Penalidad: ${penalidad_anterior}",
            nuevo_valor=f"Estado: {cancelacion.estado}, Penalidad: ${cancelacion.penalidad}"
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


# =========================
# VISTA PÚBLICA
# =========================

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
        'usuario/reservas.html',
        context
    )


@login_required(login_url='login')
def carrito_view(request):
    reservas_pendientes = Reserva.objects.filter(usuario=request.user, estado__in=['pendiente', 'Pendiente']).select_related('paquete').order_by('-id')
    context = {
        'reservas': reservas_pendientes
    }
    return render(request, 'usuario/carrito.html', context)


@login_required(login_url='login')
def comprobante_reserva_html(request, reserva_id):
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
    context = {
        'reserva': reserva,
    }
    return render(request, 'usuario/comprobante_reserva.html', context)


@login_required(login_url='login')
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
    return render(request, 'usuario/comprobante_multiple.html', context)


@login_required
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

        crear_notificacion_sistema(
            usuario=request.user,
            accion="NUEVA RESERVA CLIENTE",
            tabla_afectada="Reservas",
            observacion=f"Reserva #{reserva.id} solicitada por el usuario para el paquete '{paquete.nombre}'.",
            valor_anterior="Ninguno (Nueva Reserva)",
            nuevo_valor=f"Fecha: {fecha_date}, Adultos: {adultos}, Menores: {menores}"
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
    mis_confirmadas = Reserva.objects.filter(
        usuario=request.user, 
        estado='confirmada'
    ).select_related('paquete').order_by('-id')
    
    return render(request, 'usuario/mis_facturas.html', {
        'reservas': mis_confirmadas
    })


@login_required(login_url='login')
def ver_factura(request, reserva_id):
    from django.urls import reverse
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    if not request.user.is_staff and reserva.usuario != request.user:
        messages.error(request, "No tienes permiso para acceder a esta factura.")
        return redirect('mis_reservas_usuario')
    
    if reserva.estado != 'confirmada':
        messages.error(request, "La factura solo está disponible para reservas confirmadas y pagadas.")
        return redirect('mis_reservas_usuario')
        
    comprobante = reserva if reserva.estado_pago == 'aprobado' else None
    metodo_pago = comprobante.banco_origen_pago if comprobante else "Transferencia Bancaria"
    
    abs_url = request.build_absolute_uri(reverse('ver_factura', args=[reserva.id]))
    qr_base64 = get_qr_base64(abs_url)
    
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
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
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