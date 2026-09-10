from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.contrib import messages
from App.forms.tarifa.forms import TarifaForm
from App.utils import crear_notificacion_sistema
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django import forms
from App.models import Tarifa, Paquete, Temporada


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin para asegurar que solo usuarios autenticados con permisos
    de staff/administrador puedan acceder a las vistas administrativas.
    """
    def test_func(self):
        return self.request.user.is_active and self.request.user.is_staff


# ==========================================
# TARIFAS (ADMINISTRACIÓN)
# ==========================================

class TarifaListView(StaffRequiredMixin, ListView):
    model = Tarifa
    template_name = 'admin/tarifa/tarifas.html'
    context_object_name = 'tarifas'

    def get_queryset(self):
        queryset = super().get_queryset().select_related('paquete', 'temporada')
        paquete_id = self.request.GET.get('paquete', '').strip()
        if paquete_id:
            try:
                p_id = int(paquete_id)
                if p_id > 0:
                    queryset = queryset.filter(paquete_id=p_id)
            except (ValueError, TypeError):
                pass
        return queryset.order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stats = Tarifa.objects.aggregate(
            total=Count('id'),
            activas=Count('id', filter=Q(estado=True)),
            inactivas=Count('id', filter=Q(estado=False))
        )
        context.update(stats)
        context['stats_list'] = [
            ('Total Tarifas', stats['total'], 'text-dark'),
            ('Activas', stats['activas'], 'text-success'),
            ('Inactivas', stats['inactivas'], 'text-danger'),
        ]
        context['paquetes'] = Paquete.objects.all()
        context['paquete_seleccionado'] = self.request.GET.get('paquete', '')
        return context


class TarifaCreateView(StaffRequiredMixin, CreateView):
    model = Tarifa
    form_class = TarifaForm
    template_name = 'admin/tarifa/agregar_tarifa.html'
    success_url = reverse_lazy('listar_tarifas')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for name, field in form.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            else:
                field.widget.attrs.update({'class': 'form-control'})
        return form

    def form_valid(self, form):
        response = super().form_valid(form)
        crear_notificacion_sistema(
            usuario=self.request.user,
            accion="NUEVA TARIFA CREADA",
            tabla_afectada="Tarifas",
            observacion=f"Se ha registrado una tarifa para '{self.object.paquete.nombre}' en la temporada '{self.object.temporada.nombre}'.",
            valor_anterior="Ninguno (Registro Nuevo)",
            nuevo_valor=f"Adulto: ${self.object.precio_adulto}, Menor: ${self.object.precio_menor}"
        )
        return response


class TarifaUpdateView(StaffRequiredMixin, UpdateView):
    model = Tarifa
    form_class = TarifaForm
    template_name = 'admin/tarifa/editar_tarifa.html'
    success_url = reverse_lazy('listar_tarifas')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for name, field in form.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.Select):
                field.widget.attrs.update({'class': 'form-select'})
            else:
                field.widget.attrs.update({'class': 'form-control'})
        return form

    def form_valid(self, form):
        tarifa_antigua = self.get_object()
        valor_viejo = f"Paquete: {tarifa_antigua.paquete.nombre}, Temporada: {tarifa_antigua.temporada.nombre}, Adulto: ${tarifa_antigua.precio_adulto}, Menor: ${tarifa_antigua.precio_menor}, Estado: {'Activa' if tarifa_antigua.estado else 'Inactiva'}"

        response = super().form_valid(form)

        valor_nuevo = f"Paquete: {self.object.paquete.nombre}, Temporada: {self.object.temporada.nombre}, Adulto: ${self.object.precio_adulto}, Menor: ${self.object.precio_menor}, Estado: {'Activa' if self.object.estado else 'Inactiva'}"

        crear_notificacion_sistema(
            usuario=self.request.user,
            accion="TARIFA MODIFICADA",
            tabla_afectada="Tarifas",
            observacion=f"Los datos de la tarifa de '{self.object.paquete.nombre}' ({self.object.temporada.nombre}) han sido actualizados.",
            valor_anterior=valor_viejo,
            nuevo_valor=valor_nuevo
        )
        return response


class TarifaDeleteView(StaffRequiredMixin, DeleteView):
    model = Tarifa
    template_name = 'admin/tarifa/eliminar_tarifa.html'
    success_url = reverse_lazy('listar_tarifas')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        nombre_paquete = self.object.paquete.nombre
        nombre_temporada = self.object.temporada.nombre
        valor_viejo = f"ID: {self.object.id}, Paquete: {nombre_paquete}, Temporada: {nombre_temporada}, Adulto: ${self.object.precio_adulto}, Menor: ${self.object.precio_menor}"

        response = super().delete(request, *args, **kwargs)

        crear_notificacion_sistema(
            usuario=request.user,
            accion="TARIFA ELIMINADA",
            tabla_afectada="Tarifas",
            observacion=f"Se ha eliminado del sistema la tarifa de '{nombre_paquete}' para la temporada '{nombre_temporada}'.",
            valor_anterior=valor_viejo,
            nuevo_valor="Registro Eliminado"
        )
        return response

