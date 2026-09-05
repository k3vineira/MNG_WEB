from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import render, get_object_or_404, redirect
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Count, Q
from datetime import date, timedelta, datetime
import json
from App.models import Reserva, Paquete, Tarifa
from App.forms.reserva.forms import ReservaForm
from App.utils import (
    plantilla_reserva_html,
    plantilla_cancelacion_html,
    enviar_correo_html_monagua,
    crear_notificacion_sistema,
    StaffRequiredMixin
)


# ==========================================
# ADMINISTRACIÓN DE RESERVAS
# ==========================================

@method_decorator(login_required(login_url='login'), name='dispatch')
class ReservaListView(StaffRequiredMixin, ListView):
    """Vista para listar reservas en el panel de administración con estadísticas por estado."""
    model = Reserva
    template_name = 'admin/reservas/reservas.html'
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


@login_required(login_url='login')
def cambiar_estado_reserva(request, reserva_id):
    """Vista rápida AJAX para cambiar el estado de una reserva (Administrador)."""
    if not (request.user.is_staff or getattr(request.user, 'rol', None) == 1):
        return JsonResponse({'success': False, 'error': 'Permiso denegado.'}, status=403)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            nuevo_estado = data.get('estado')

            reserva = get_object_or_404(Reserva, id=reserva_id)
            valid_states = [c[0] for c in Reserva.ESTADO_CHOICES]
            if nuevo_estado not in valid_states:
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


@method_decorator(login_required(login_url='login'), name='dispatch')
class ReservaCreateView(StaffRequiredMixin, SuccessMessageMixin, CreateView):
    """Vista para registrar manualmente una reserva desde el panel de administración."""
    model = Reserva
    form_class = ReservaForm
    template_name = 'admin/reservas/agregar_reserva.html'
    success_url = reverse_lazy('listar_reservas')
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


@method_decorator(login_required(login_url='login'), name='dispatch')
class ReservaUpdateView(StaffRequiredMixin, UpdateView):
    """Vista para editar una reserva existente desde el panel de administración."""
    model = Reserva
    form_class = ReservaForm
    template_name = 'admin/reservas/editar_reserva.html'
    success_url = reverse_lazy('listar_reservas')

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


@method_decorator(login_required(login_url='login'), name='dispatch')
class ReservaDeleteView(StaffRequiredMixin, DeleteView):
    """Vista para eliminar una reserva desde el panel de administración."""
    model = Reserva
    template_name = 'admin/reservas/eliminar_reserva.html'
    success_url = reverse_lazy('listar_reservas')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        reserva_id = self.object.id
        valor_viejo = f"ID: {self.object.id}, Cliente: {self.object.usuario}, Paquete: {self.object.paquete.nombre}, Estado: {self.object.estado_reserva}"

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


# ==========================================
# RESERVAS DEL TURISTA / CLIENTE
# ==========================================

@login_required(login_url='login')
def mis_reservas_usuario(request):
    """Lista las reservas realizadas por el usuario logueado."""
    mis_reservas = Reserva.objects.filter(usuario=request.user)\
        .select_related('paquete')\
        .order_by('-id')

    context = {
        'reservas': mis_reservas
    }
    return render(request, 'usuario/mis_reservas.html', context)


def reservas_view(request):
    """Vista pública para iniciar el proceso de reserva de un paquete turístico."""
    paquetes = Paquete.objects.filter(estado=True)
    paquete_id = request.GET.get('paquete_id')
    paquete = None
    if paquete_id:
        paquete = get_object_or_404(Paquete, id=paquete_id, estado=True)

    context = {
        'paquetes': paquetes,
        'paquete': paquete
    }

    return render(request, 'usuario/reservas.html', context)


@login_required(login_url='login')
def carrito_view(request):
    """Muestra las reservas en estado pendiente del cliente como un carrito de compras."""
    reservas_pendientes = Reserva.objects.filter(
        usuario=request.user,
        estado_reserva__in=['pendiente', 'Pendiente']
    ).select_related('paquete').order_by('-id')

    context = {
        'reservas': reservas_pendientes
    }
    return render(request, 'usuario/carrito.html', context)


@login_required(login_url='login')
def comprobante_reserva_html(request, reserva_id):
    """Muestra el comprobante individual de una reserva en formato HTML."""
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)
    context = {
        'reserva': reserva,
    }
    return render(request, 'usuario/comprobante_reserva.html', context)


@login_required(login_url='login')
def comprobante_multiple(request):
    """Genera la vista de resumen para procesar múltiples reservas seleccionadas."""
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


@login_required(login_url='login')
def guardar_reserva(request, paquete_id):
    """Procesa el formulario del usuario para crear y guardar una nueva reserva."""
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
            temporada__fecha_fin__gte=fecha_date,
            estado=True
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
            punto_encuentro=paquete.punto_encuentro or "Por definir",
            hora_encuentro=paquete.hora_encuentro,
            estado=reserva.estado_reserva,
            reserva_id=reserva.id,
            monto_total=str(reserva.monto_total)
        )

        try:
            enviar_correo_html_monagua(asunto, mensaje_texto, request.user.email, html_bonito)
        except Exception as e:
            print(f"Error enviando correo de confirmación de reserva: {e}")

        messages.success(
            request, "¡Tu reserva ha sido creada y confirmada por correo electrónico!")
        return redirect('mis_reservas_usuario')

    return redirect('reservas')


@login_required(login_url='login')
def cancelar_reserva_usuario(request, reserva_id):
    """Cancela una reserva activa del usuario cambiando su estado a cancelada y registrando el motivo."""
    reserva = get_object_or_404(Reserva, id=reserva_id, usuario=request.user)

    if reserva.estado_reserva == 'cancelada':
        messages.warning(request, "Esta reserva ya se encuentra cancelada.")
        return redirect('mis_reservas_usuario')

    if request.method == 'POST':
        motivo = request.POST.get('motivo', '').strip()
        if not motivo:
            messages.error(request, "Por favor especifica un motivo de cancelación.")
            return redirect('mis_reservas_usuario')

        estado_anterior = reserva.estado_reserva
        reserva.estado_reserva = 'cancelada'
        reserva.motivo_cancelacion = motivo
        reserva.save()

        crear_notificacion_sistema(
            usuario=request.user,
            accion="RESERVA CANCELADA",
            tabla_afectada="Reservas",
            observacion=f"El usuario canceló la reserva #{reserva.id}. Motivo: {motivo}",
            valor_anterior=f"Estado: {estado_anterior}",
            nuevo_valor="Estado: cancelada"
        )

        nombre_cliente = request.user.first_name or request.user.username
        asunto = f"Reserva #{reserva.id} Cancelada - Monagua"
        mensaje_texto = f"Hola {nombre_cliente}, tu reserva para {reserva.paquete.nombre} ha sido cancelada."

        html_cancelacion = plantilla_cancelacion_html(
            nombre_cliente=nombre_cliente,
            paquete=reserva.paquete.nombre,
            estado='cancelada',
            penalidad="0.00"
        )

        try:
            enviar_correo_html_monagua(asunto, mensaje_texto, request.user.email, html_cancelacion)
        except Exception as e:
            print(f"Error al enviar correo de cancelación: {e}")

        messages.success(request, "Tu reserva ha sido cancelada correctamente.")
        return redirect('mis_reservas_usuario')

    return render(request, 'usuario/confirmar_cancelacion.html', {'reserva': reserva})