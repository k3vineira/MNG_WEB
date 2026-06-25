from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import render
from .models import Reserva, Cancelacion
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from catalogo.models import Paquete
from .forms import ReservaForm, CancelacionForm
from decimal import Decimal, InvalidOperation
from django.core.mail import send_mail
from datetime import datetime
from catalogo.models import Tarifa
from django.conf import settings
from django.contrib import messages
from django.db.models import Count, Q
from core.utils import plantilla_reserva_html, plantilla_cancelacion_html, enviar_correo_html_monagua
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse
from django.template.loader import render_to_string

# =========================
# RESERVAS ADMIN
# =========================


class ReservaListView(ListView):
    model = Reserva
    template_name = 'admin/reservas/reservas.html'
    context_object_name = 'reservas'

    def get_queryset(self):
        return Reserva.objects.exclude(estado='cancelada').order_by('-id')

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
        return context


class ReservaCreateView(SuccessMessageMixin, CreateView):
    model = Reserva
    form_class = ReservaForm
    template_name = 'admin/reservas/agregar_reserva.html'
    success_url = ('listar_reservas')

    success_message = "¡La reserva ha sido creada con éxito!"

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        return super().form_valid(form)


class ReservaUpdateView(UpdateView):
    model = Reserva
    form_class = ReservaForm
    # fields = ['usuario','paquete','fecha','numero_adultos','numero_menores','estado', ]
    template_name = 'admin/reservas/editar_reserva.html'
    success_url = reverse_lazy('listar_reservas')


class ReservaDeleteView(DeleteView):
    model = Reserva
    template_name = 'admin/reservas/eliminar_reserva.html'
    success_url = reverse_lazy('listar_reservas')


@login_required(login_url='login')
def mis_reservas_usuario(request):
    # Mostrar todas las reservas del usuario, incluyendo aquellas canceladas,
    # para que el usuario pueda ver su historial y el estado real de cada reserva.
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
        reserva_id = self.request.GET.get('reserva_id')
        if not reserva_id:
            messages.error(
                self.request, 'No se encontró la reserva para la cancelación.')
            return redirect('mis_cancelaciones_usuario')

        reserva = get_object_or_404(
            Reserva, id=reserva_id, usuario=self.request.user)

        if reserva.estado == 'cancelada':
            messages.warning(self.request, 'Esta reserva ya está cancelada.')
            return redirect('mis_cancelaciones_usuario')

        if Cancelacion.objects.filter(reserva=reserva, estado__in=['revision', 'aceptada']).exists():
            messages.warning(
                self.request, 'Ya existe una solicitud de cancelación activa para esta reserva.')
            return redirect('mis_cancelaciones_usuario')

        form.instance.reserva = reserva
        form.instance.usuario = self.request.user
        return super().form_valid(form)


class CancelacionUpdateView(UpdateView):
    model = Cancelacion
    form_class = CancelacionForm
    template_name = 'admin/cancelaciones/editar_cancelacion.html'
    success_url = reverse_lazy('administrar_cancelaciones')


class CancelacionDeleteView(DeleteView):
    model = Cancelacion
    template_name = 'admin/cancelaciones/eliminar_cancelacion.html'
    success_url = reverse_lazy('administrar_cancelaciones')


@login_required(login_url='login')
def mis_cancelaciones_usuario(request):
    mis_cancelaciones = Cancelacion.objects.filter(reserva__usuario=request.user)\
        .select_related('reserva__paquete')\
        .prefetch_related('reserva__comprobantes')\
        .order_by('-id')

    context = {
        'cancelaciones': mis_cancelaciones
    }
    return render(request, 'usuario/cancelaciones/mis_cancelaciones.html', context)


def administrar_cancelaciones(request):
    if request.method == 'POST':
        cancelacion_id = request.POST.get('cancelacion_id')
        cancelacion = get_object_or_404(Cancelacion, id=cancelacion_id)

        cancelacion.estado = request.POST.get('estado')

        penalidad_raw = request.POST.get('penalidad', '0').strip()
        try:
            cancelacion.penalidad = Decimal(
                penalidad_raw) if penalidad_raw else Decimal('0.00')
        except (InvalidOperation, ValueError):
            cancelacion.penalidad = Decimal('0.00')

        cancelacion.save()

        # Mantener el estado real de la reserva sin producir cambios inesperados.
        if cancelacion.estado == 'aceptada':
            cancelacion.reserva.estado = 'cancelada'
            cancelacion.reserva.save()
        elif cancelacion.estado == 'rechazada':
            # No se altera el estado original de la reserva. Si estaba confirmada, sigue confirmada;
            # si estaba pendiente, continúa pendiente hasta que el administrador defina otro comportamiento.
            cancelacion.reserva.save()
        else:
            # En revisión no se debe cambiar el estado de la reserva.
            cancelacion.reserva.save()

        nombre_cliente = (
            cancelacion.reserva.usuario.first_name
            or cancelacion.reserva.usuario.username
        )

        asunto_reserva = (
            f"Actualización de tu Reserva #{cancelacion.reserva.id} - Monagua"
        )

        if cancelacion.reserva.estado == 'cancelada':
            mensaje_reserva_texto = (
                f"Hola {nombre_cliente}, tu reserva para "
                f"{cancelacion.reserva.paquete.nombre} ha sido CANCELADA "
                "debido a la aprobación de tu solicitud."
            )
        elif cancelacion.reserva.estado == 'confirmada':
            mensaje_reserva_texto = (
                f"Hola {nombre_cliente}, tu solicitud de cancelación fue "
                f"rechazada, por lo tanto tu reserva para "
                f"{cancelacion.reserva.paquete.nombre} sigue CONFIRMADA."
            )
        else:
            mensaje_reserva_texto = (
                f"Hola {nombre_cliente}, tu reserva para "
                f"{cancelacion.reserva.paquete.nombre} está en estado: "
                f"{cancelacion.reserva.estado}."
            )

        html_reserva = plantilla_reserva_html(
            nombre_cliente=nombre_cliente,
            paquete=cancelacion.reserva.paquete.nombre,
            estado=cancelacion.reserva.estado,
            reserva_id=cancelacion.reserva.id,
            monto_total=cancelacion.reserva.monto_total
        )

        enviar_correo_html_monagua(
            asunto_reserva,
            mensaje_reserva_texto,
            cancelacion.reserva.usuario.email,
            html_reserva
        )

        asunto = "Actualización de cancelación - Monagua"

        if cancelacion.estado == 'aceptada':
            mensaje_texto = (
                f"Hola {nombre_cliente}, tu solicitud de cancelación para "
                f"{cancelacion.reserva.paquete.nombre} ha sido aceptada."
            )
        elif cancelacion.estado == 'rechazada':
            mensaje_texto = (
                f"Hola {nombre_cliente}, tu solicitud de cancelación para "
                f"{cancelacion.reserva.paquete.nombre} ha sido rechazada."
            )
        else:
            mensaje_texto = (
                f"Hola {nombre_cliente}, tu solicitud de cancelación para "
                f"{cancelacion.reserva.paquete.nombre} está en revisión."
            )

        html_cancelacion = plantilla_cancelacion_html(
            nombre_cliente=nombre_cliente,
            paquete=cancelacion.reserva.paquete.nombre,
            estado=cancelacion.estado,
            penalidad=cancelacion.penalidad
        )

        enviar_correo_html_monagua(
            asunto,
            mensaje_texto,
            cancelacion.reserva.usuario.email,
            html_cancelacion
        )

        return redirect('administrar_cancelaciones')

    stats = Cancelacion.objects.aggregate(
        total=Count('id'),
        revisando=Count('id', filter=Q(estado__in=['pendiente', 'revision'])),
        aceptadas=Count('id', filter=Q(estado__in=['confirmada', 'aceptada'])),
        rechazadas=Count('id', filter=Q(estado__in=['cancelada', 'rechazada']))
    )

    stats_list = [
        ('Total', stats['total'], 'text-dark'),
        ('En Revisión', stats['revisando'], 'text-warning'),
        ('Aceptadas', stats['aceptadas'], 'text-success'),
        ('Rechazadas', stats['rechazadas'], 'text-danger'),
    ]

    cancelaciones_raw = Cancelacion.objects.all().order_by('-id')

    for c in cancelaciones_raw:
        try:
            Decimal(str(c.penalidad))
        except (InvalidOperation, ValueError, TypeError):
            c.penalidad = Decimal('0.00')

    context = {'cancelaciones': cancelaciones_raw, 'stats_list': stats_list}
    return render(request, 'admin/cancelaciones/cancelaciones_admin.html', context)

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
    """Muestra las reservas pendientes del usuario en formato carrito y permite generar comprobante imprimible."""
    reservas_pendientes = Reserva.objects.filter(usuario=request.user, estado__in=['pendiente', 'Pendiente']).select_related('paquete').order_by('-id')
    context = {
        'reservas': reservas_pendientes
    }
    return render(request, 'usuario/carrito.html', context)


@login_required(login_url='login')
def comprobante_reserva_html(request, reserva_id):
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
            estado=reserva.estado,
            reserva_id=reserva.id,
            monto_total=reserva.monto_total
        )

        enviar_correo_html_monagua(
            asunto, mensaje_texto, request.user.email, html_bonito)

        messages.success(
            request, "¡Tu reserva ha sido creada y confirmada por correo electrónico!")
        return redirect('mis_reservas_usuario')

    return redirect('reservas')
