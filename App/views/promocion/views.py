from datetime import datetime
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q, Avg
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django import forms

from App.forms.promocion.forms import PromocionForm
from App.models import Promocion, PaquetePromocion, Paquete
from App.utils import crear_notificacion_sistema


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin para asegurar que solo usuarios autenticados con permisos
    de staff/administrador puedan acceder a las vistas administrativas de promociones.
    """
    def test_func(self):
        return self.request.user.is_active and self.request.user.is_staff


def staff_check(user):
    return user.is_authenticated and user.is_active and user.is_staff


# ==============================================================================
# 1. LISTADO Y ADMINISTRACIÓN DE PROMOCIONES
# ==============================================================================
class PromocionListView(StaffRequiredMixin, ListView):
    model = Promocion
    template_name = 'admin/promocion/promociones.html'
    context_object_name = 'promociones'

    def get_queryset(self):
        queryset = Promocion.objects.prefetch_related('paquetepromocion_set__paquete').all()

        # Filtro por término de búsqueda (nombre, código promoción, cupón)
        q = self.request.GET.get('q', '').strip()
        if q:
            queryset = queryset.filter(
                Q(nombre__icontains=q) |
                Q(codigo_promocion__icontains=q) |
                Q(codigo_cupon__icontains=q) |
                Q(descripcion__icontains=q)
            )

        # Filtro por estado activo/inactivo
        estado = self.request.GET.get('estado', '').strip()
        if estado == 'activas':
            queryset = queryset.filter(activa=True)
        elif estado == 'inactivas':
            queryset = queryset.filter(activa=False)

        # Filtro por fechas
        fecha_inicio = self.request.GET.get('fecha_inicio', '').strip()
        fecha_fin = self.request.GET.get('fecha_fin', '').strip()

        if fecha_inicio:
            try:
                f_ini = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_inicio__gte=f_ini)
            except ValueError:
                pass

        if fecha_fin:
            try:
                f_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_fin__lte=f_fin)
            except ValueError:
                pass

        return queryset.order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        stats = Promocion.objects.aggregate(
            total=Count('id'),
            activas=Count('id', filter=Q(activa=True)),
            inactivas=Count('id', filter=Q(activa=False)),
            avg_descuento=Avg('porcentaje_descuento')
        )
        
        avg_desc_valor = round(stats['avg_descuento'] or 0)

        context['stats_list'] = [
            ('Total Promociones', stats['total'], 'text-dark', 'bi-megaphone'),
            ('Activas', stats['activas'], 'text-success', 'bi-check-circle-fill'),
            ('Inactivas', stats['inactivas'], 'text-danger', 'bi-x-circle-fill'),
            ('Descuento Promedio', f"{avg_desc_valor}%", 'text-primary', 'bi-percent'),
        ]
        context['q'] = self.request.GET.get('q', '')
        context['estado_filtro'] = self.request.GET.get('estado', '')
        context['fecha_inicio'] = self.request.GET.get('fecha_inicio', '')
        context['fecha_fin'] = self.request.GET.get('fecha_fin', '')
        return context


# ==============================================================================
# 2. CREACIÓN DE PROMOCIÓN
# ==============================================================================
class PromocionCreateView(StaffRequiredMixin, CreateView):
    model = Promocion
    form_class = PromocionForm
    template_name = 'admin/promocion/agregar_promocion.html'
    success_url = reverse_lazy('gestion_promociones')

    def form_valid(self, form):
        response = super().form_valid(form)
        promocion = self.object

        # Vincular los paquetes turísticos seleccionados y calcular valores con descuento
        paquetes_seleccionados = form.cleaned_data.get('paquetes', [])
        descuento_factor = Decimal(promocion.porcentaje_descuento) / Decimal(100)

        for paquete in paquetes_seleccionados:
            tarifa = paquete.tarifas.filter(estado=True).first()
            if tarifa:
                precio_ad = tarifa.precio_adulto
                precio_me = tarifa.precio_menor
                val_adulto = round(precio_ad * (Decimal(1) - descuento_factor), 2)
                val_menor = round(precio_me * (Decimal(1) - descuento_factor), 2)
            else:
                val_adulto = Decimal('0.00')
                val_menor = Decimal('0.00')

            PaquetePromocion.objects.create(
                paquete=paquete,
                promocion=promocion,
                valor_adulto_condescuento=val_adulto,
                valor_menor_condescuento=val_menor
            )

        # Auditoría / Notificación del sistema
        crear_notificacion_sistema(
            usuario=self.request.user,
            accion="NUEVA PROMOCIÓN CREADA",
            tabla_afectada="Promociones",
            observacion=f"Se ha registrado con éxito la promoción '{promocion.nombre}' ({promocion.codigo_promocion}) con {promocion.porcentaje_descuento}% de descuento.",
            valor_anterior="Ninguno (Registro Nuevo)",
            nuevo_valor=f"Nombre: {promocion.nombre}, Código: {promocion.codigo_promocion}, Descuento: {promocion.porcentaje_descuento}%, Paquetes vinculados: {paquetes_seleccionados.count()}"
        )

        messages.success(self.request, f"Promoción '{promocion.nombre}' registrada correctamente.")
        return response


# ==============================================================================
# 3. MODIFICACIÓN DE PROMOCIÓN
# ==============================================================================
class PromocionUpdateView(StaffRequiredMixin, UpdateView):
    model = Promocion
    form_class = PromocionForm
    template_name = 'admin/promocion/editar_promocion.html'
    success_url = reverse_lazy('gestion_promociones')

    def form_valid(self, form):
        promo_antigua = self.get_object()
        valor_viejo = (
            f"Nombre: {promo_antigua.nombre}, Código: {promo_antigua.codigo_promocion}, "
            f"Descuento: {promo_antigua.porcentaje_descuento}%, Activa: {promo_antigua.activa}"
        )

        response = super().form_valid(form)
        promocion = self.object

        # Actualizar paquetes asociados en PaquetePromocion
        nuevos_paquetes = form.cleaned_data.get('paquetes', [])
        descuento_factor = Decimal(promocion.porcentaje_descuento) / Decimal(100)

        # Eliminar las relaciones que ya no fueron seleccionadas
        PaquetePromocion.objects.filter(promocion=promocion).exclude(paquete__in=nuevos_paquetes).delete()

        # Crear o actualizar las relaciones para los paquetes seleccionados
        for paquete in nuevos_paquetes:
            tarifa = paquete.tarifas.filter(estado=True).first()
            if tarifa:
                precio_ad = tarifa.precio_adulto
                precio_me = tarifa.precio_menor
                val_adulto = round(precio_ad * (Decimal(1) - descuento_factor), 2)
                val_menor = round(precio_me * (Decimal(1) - descuento_factor), 2)
            else:
                val_adulto = Decimal('0.00')
                val_menor = Decimal('0.00')

            PaquetePromocion.objects.update_or_create(
                paquete=paquete,
                promocion=promocion,
                defaults={
                    'valor_adulto_condescuento': val_adulto,
                    'valor_menor_condescuento': val_menor
                }
            )

        # Auditoría / Notificación del sistema
        valor_nuevo = (
            f"Nombre: {promocion.nombre}, Código: {promocion.codigo_promocion}, "
            f"Descuento: {promocion.porcentaje_descuento}%, Activa: {promocion.activa}, "
            f"Paquetes vinculados: {nuevos_paquetes.count()}"
        )
        crear_notificacion_sistema(
            usuario=self.request.user,
            accion="PROMOCIÓN MODIFICADA",
            tabla_afectada="Promociones",
            observacion=f"La promoción '{promocion.nombre}' ha sido modificada satisfactoriamente.",
            valor_anterior=valor_viejo,
            nuevo_valor=valor_nuevo
        )

        messages.success(self.request, f"Promoción '{promocion.nombre}' actualizada correctamente.")
        return response


# ==============================================================================
# 4. ELIMINACIÓN DE PROMOCIÓN
# ==============================================================================
class PromocionDeleteView(StaffRequiredMixin, DeleteView):
    model = Promocion
    template_name = 'admin/promocion/eliminar_promocion.html'
    success_url = reverse_lazy('gestion_promociones')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        nombre_promo = self.object.nombre
        codigo_promo = self.object.codigo_promocion
        valor_viejo = f"ID: {self.object.id}, Nombre: {nombre_promo}, Código: {codigo_promo}"

        response = super().delete(request, *args, **kwargs)

        crear_notificacion_sistema(
            usuario=request.user,
            accion="PROMOCIÓN ELIMINADA",
            tabla_afectada="Promociones",
            observacion=f"Se ha eliminado permanentemente la promoción '{nombre_promo}' ({codigo_promo}).",
            valor_anterior=valor_viejo,
            nuevo_valor="Registro Eliminado"
        )

        messages.success(request, f"La promoción '{nombre_promo}' fue eliminada del sistema.")
        return response


# ==============================================================================
# 5. CAMBIO RÁPIDO DE ESTADO (ACTIVAR / DESACTIVAR)
# ==============================================================================
@login_required
@user_passes_test(staff_check)
def toggle_estado_promocion(request, pk):
    """Permite alternar el estado activa (True/False) de una promoción de manera ágil."""
    promocion = get_object_or_404(Promocion, pk=pk)
    estado_previo = promocion.activa
    promocion.activa = not estado_previo
    promocion.save(update_fields=['activa'])

    nuevo_estado_str = "Activa" if promocion.activa else "Inactiva"

    crear_notificacion_sistema(
        usuario=request.user,
        accion="ESTADO PROMOCIÓN ACTUALIZADO",
        tabla_afectada="Promociones",
        observacion=f"El estado de la promoción '{promocion.nombre}' cambió a {nuevo_estado_str}.",
        valor_anterior=f"Activa: {estado_previo}",
        nuevo_valor=f"Activa: {promocion.activa}"
    )

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
        return JsonResponse({
            'success': True,
            'id': promocion.pk,
            'activa': promocion.activa,
            'label': nuevo_estado_str
        })

    messages.info(request, f"La promoción '{promocion.nombre}' ahora está {nuevo_estado_str}.")
    return redirect('gestion_promociones')
