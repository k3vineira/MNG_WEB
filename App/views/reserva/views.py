from datetime import date, timedelta
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, View
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.contrib import messages
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.core.mail import send_mail
from django.conf import settings

from App.models import Reserva
from App.forms.reserva.forms import ReservaForm
from core.decoradores import requiere_administrador
from App.utils import (
    plantilla_reserva_html,
    enviar_correo_html_monagua,
    enviar_correo_confirmacion_con_factura,
    crear_notificacion_sistema
)


# -------------------------------------------------------------------
# CRUD RESERVAS - ADMINISTRACIÓN
# -------------------------------------------------------------------

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


@method_decorator(requiere_administrador, name='dispatch')
class ReservaCreateView(SuccessMessageMixin, CreateView):
    model = Reserva
    form_class = ReservaForm
    template_name = 'admin/reservas/agregar_reserva.html'
    success_url = reverse_lazy('listar_reservas')
    success_message = "¡La reserva ha sido creada con éxito!"

    def form_valid(self, form):
        # La validación de 5 días de anticipación y de cupos se realiza automáticamente en ReservaForm
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

    def form_valid(self, form):
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


@method_decorator(requiere_administrador, name='dispatch')
class ReservaCancelarView(View):
    """Acción del CRUD para cambiar lógicamente el estado a 'cancelada' desde el panel admin."""
    def post(self, request, pk):
        reserva = get_object_or_404(Reserva, pk=pk)
        if reserva.estado == 'cancelada':
            messages.warning(request, f"La reserva #{reserva.id} ya se encuentra cancelada.")
            return redirect('listar_reservas')

        estado_anterior = reserva.estado
        reserva.estado = 'cancelada'
        reserva.save()

        crear_notificacion_sistema(
            usuario=request.user,
            accion="RESERVA CANCELADA",
            tabla_afectada="Reservas",
            observacion=f"El administrador canceló la reserva #{reserva.id}.",
            valor_anterior=f"Estado: {estado_anterior}",
            nuevo_valor="Estado: cancelada"
        )

        nombre_cliente = reserva.usuario.first_name or reserva.usuario.username
        asunto = f"Tu Reserva #{reserva.id} ha sido CANCELADA - Monagua"
        mensaje_texto = f"Hola {nombre_cliente}, tu reserva para {reserva.paquete.nombre} ha sido cancelada."
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
            print(f"Error al enviar correo de cancelación: {e}")

        messages.success(request, f"La reserva #{reserva.id} ha sido cancelada correctamente.")
        return redirect('listar_reservas')


@method_decorator(requiere_administrador, name='dispatch')
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
            observacion=f"Se ha eliminado físicamente del sistema la reserva #{reserva_id}.",
            valor_anterior=valor_viejo,
            nuevo_valor="Registro Eliminado"
        )
        return response


# -------------------------------------------------------------------
# VISTAS DE USUARIO
# -------------------------------------------------------------------

@login_required(login_url='login')
def mis_reservas_usuario(request):
    mis_reservas = Reserva.objects.filter(usuario=request.user)\
        .select_related('paquete', 'pago')\
        .prefetch_related('cancelaciones')\
        .order_by('-id')

    context = {
        'reservas': mis_reservas
    }
    return render(request, 'usuario/mis_reservas.html', context)


@login_required(login_url='login')
def cancelar_reserva_usuario(request, pk):
    """Permite al cliente cancelar su propia reserva dentro del límite de 3 días tras realizarla."""
    reserva = get_object_or_404(Reserva, pk=pk, usuario=request.user)

    if reserva.estado == 'cancelada':
        messages.warning(request, "Esta reserva ya fue cancelada previamente.")
        return redirect('mis_reservas_usuario')

    # --- REGLA DE NEGOCIO: Máximo 3 días para cancelar desde que se creó la reserva ---
    # Busca 'fecha_creacion' o 'created_at' en tu modelo Reserva
    fecha_registro = getattr(reserva, 'fecha_creacion', None) or getattr(reserva, 'created_at', None)

    if fecha_registro:
        fecha_registro_date = fecha_registro.date() if hasattr(fecha_registro, 'date') else fecha_registro
        dias_transcurridos = (date.today() - fecha_registro_date).days

        if dias_transcurridos > 3:
            messages.error(
                request,
                "Han pasado más de 3 días desde que realizaste la reserva. Ya no es posible descartarla."
            )
            return redirect('mis_reservas_usuario')

    estado_anterior = reserva.estado
    reserva.estado = 'cancelada'
    reserva.save()

    crear_notificacion_sistema(
        usuario=request.user,
        accion="CANCELACIÓN DE RESERVA POR CLIENTE",
        tabla_afectada="Reservas",
        observacion=f"El cliente canceló su reserva #{reserva.id}.",
        valor_anterior=f"Estado: {estado_anterior}",
        nuevo_valor="Estado: cancelada"
    )

    messages.success(request, f"Tu reserva #{reserva.id} ha sido cancelada exitosamente.")
    return redirect('mis_reservas_usuario')


def enviar_correo_monagua(asunto, mensaje, destinatario):
    send_mail(
        asunto,
        mensaje,
        settings.EMAIL_HOST_USER,
        [destinatario],
        fail_silently=False,
    )