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
            
            estado_anterior = reserva.estado_reserva
            reserva.estado_reserva = nuevo_estado
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
class CrearReservaAdminView(SuccessMessageMixin, CreateView):
    model = Reserva
    form_class = ReservaForm
    template_name = 'admin/reserva/agregar_reserva.html'
    success_url = reverse_lazy('gestion_reservas')
    success_message = "¡La reserva ha sido creada con éxito!"

    def form_valid(self, form):
        adultos = form.cleaned_data.get('numero_adultos', 0)
        menores = form.cleaned_data.get('numero_menores', 0)
        fecha = form.cleaned_data.get('fecha_inicio')

        if adultos < 1:
            form.add_error('numero_adultos', 'Debe haber al menos 1 adulto en la reserva.')
            return self.form_invalid(form)

        if menores < 0:
            form.add_error('numero_menores', 'El número de menores no puede ser negativo.')
            return self.form_invalid(form)

        if fecha and fecha < date.today():
            form.add_error('fecha_inicio', 'No puedes crear reservas en fechas pasadas.')
            return self.form_invalid(form)

        response = super().form_valid(form)

        crear_notificacion_sistema(
            usuario=self.request.user,
            accion="NUEVA RESERVA CREADA",
            tabla_afectada="Reservas",
            observacion=f"Se ha registrado manualmente la reserva #{self.object.id} para el paquete '{self.object.paquete.nombre}'.",
            valor_anterior="Ninguno (Registro Nuevo)",
            nuevo_valor=f"Cliente: {self.object.usuario.get_full_name() or self.object.usuario.username}, Fecha: {self.object.fecha_inicio}, Adultos: {self.object.numero_adultos}, Menores: {self.object.numero_menores}"
        )

        return response


@method_decorator(requiere_administrador, name='dispatch')
class EditarReservaAdminView(UpdateView):
    model = Reserva
    form_class = ReservaForm
    template_name = 'admin/reserva/editar_reserva.html'
    success_url = reverse_lazy('gestion_reservas')

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
        valor_viejo = f"Estado: {reserva_antigua.estado_reserva}, Fecha: {reserva_antigua.fecha_inicio}, Adultos: {reserva_antigua.numero_adultos}, Menores: {reserva_antigua.numero_menores}"

        response = super().form_valid(form)
        reserva = self.object
        nombre_cliente = reserva.usuario.first_name or reserva.usuario.username
        
        valor_nuevo = f"Estado: {reserva.estado_reserva}, Fecha: {reserva.fecha_inicio}, Adultos: {reserva.numero_adultos}, Menores: {reserva.numero_menores}"

        if reserva.estado_reserva in ['confirmada', 'cancelada']:
            crear_notificacion_sistema(
                usuario=self.request.user,
                accion=f"RESERVA {reserva.estado_reserva.upper()}",
                tabla_afectada="Reservas",
                observacion=f"La reserva #{reserva.id} para el paquete '{reserva.paquete.nombre}' ha cambiado a {reserva.estado_reserva}.",
                valor_anterior=valor_viejo,
                nuevo_valor=valor_nuevo
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
@solo_turistas_requerido
def mis_reservas_usuario(request):
    mis_reservas = Reserva.objects.filter(usuario=request.user)\
        .select_related('paquete')\
                .order_by('-id')

    context = {
        'reservas': mis_reservas
    }
    return render(request, 'admin/reserva/mis_reservas.html', context)


@login_required(login_url='login')
@solo_turistas_requerido
def cancelar_reserva_usuario(request, reserva_id=None, pk=None):
    """Procesa la cancelación enviada desde el modal, calcula la penalidad numérica y aplica políticas."""
    
    # 1. Validación de método HTTP (Redirige a la lista si no es POST)
    if request.method != 'POST':
        return redirect('mis_reservas_usuario')

    real_id = reserva_id or pk
    reserva = get_object_or_404(Reserva, id=real_id, usuario=request.user)

    # 2. Validar si ya se encuentra cancelada o en proceso
    if reserva.estado_reserva in ['cancelada', 'pendiente']:
        messages.warning(request, "Esta reserva ya cuenta con una solicitud de cancelación procesada o en revisión.")
        return redirect('mis_cancelaciones')

    # 3. Control de días desde el registro (Usando el campo 'fecha_registro' del modelo)
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

    # 5. Cálculo dinámico y numérico de la penalidad según la fecha de inicio del tour
    monto_total = float(reserva.monto_total or 0)
    fecha_tour = getattr(reserva, 'fecha_inicio', None)
    
    penalidad_calculada = 0.0
    politica_reembolso = "Sujeto a evaluación administrativa."

    if fecha_tour:
        dias_para_tour = (fecha_tour - date.today()).days
        if dias_para_tour > 15:
            penalidad_calculada = monto_total * 0.10
            politica_reembolso = "Favorable (Reembolso del 90% / Penalidad del 10%)."
        elif 5 <= dias_para_tour <= 14:
            penalidad_calculada = monto_total * 0.50
            politica_reembolso = "Parcial (Reembolso del 50% / Penalidad del 50%)."
        else:
            penalidad_calculada = monto_total * 1.00
            politica_reembolso = "Sin reembolso (Menos de 5 días / No-Show)."

    # 6. Actualización del objeto Reserva
    estado_anterior = reserva.estado_reserva
    reserva.motivo_cancelacion = motivo
    reserva.penalidad = penalidad_calculada
    reserva.estado_reserva = 'pendiente'  # Queda en revisión por el administrador
    reserva.save()

    # 7. Notificación en bitácora / sistema
    try:
        crear_notificacion_sistema(
            usuario=request.user,
            accion="CANCELACIÓN DE RESERVA POR CLIENTE",
            tabla_afectada="Reservas",
            observacion=f"Solicitud de cancelación reserva #{reserva.id}. Motivo: '{motivo}'. Penalidad calculada: COP ${penalidad_calculada:,.0f}",
            valor_anterior=f"Estado: {estado_anterior}",
            nuevo_valor="Estado: pendiente"
        )
    except Exception:
        pass  # Evita interrumpir el flujo si falla el registro de auditoría

    # 8. Envío de correo de confirmación
    try:
        asunto = f"Solicitud de Cancelación - Reserva #{reserva.id} | Monagua"
        mensaje = (
            f"Hola {request.user.get_full_name() or request.user.username},\n\n"
            f"Hemos recibido tu solicitud de cancelación para la reserva #{reserva.id}.\n\n"
            f"- Motivo: {motivo}\n"
            f"- Penalidad estimada: COP ${penalidad_calculada:,.0f}\n"
            f"- Política aplicada: {politica_reembolso}\n\n"
            f"Tu solicitud está en estado 'Pendiente' mientras el administrador valida la penalidad y los comprobantes.\n\n"
            f"Atentamente,\nEquipo Monagua"
        )
        send_mail(asunto, mensaje, None, [request.user.email], fail_silently=True)
    except Exception:
        pass

    messages.success(request, f"Solicitud enviada exitosamente para la reserva #{reserva.id}. Está pendiente de revisión.")
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
        estado_reserva__iexact='cancelada'
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
    reserva = get_object_or_404(Reserva, id=reserva_id)
    
    if not request.user.is_staff and reserva.usuario != request.user:
        messages.error(request, "No tienes permiso para acceder a esta factura.")
        return redirect('mis_reservas_usuario')
    
    if reserva.estado_reserva != 'confirmada':
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
        'fecha_emision': reserva.fecha_registro.strftime('%d/%m/%Y') if hasattr(reserva, 'fecha_registro') and reserva.fecha_registro else (reserva.fecha_inicio.strftime('%d/%m/%Y') if reserva.fecha_inicio else ''),
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