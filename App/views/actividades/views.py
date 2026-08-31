from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.contrib import messages
from App.forms.actividades.forms import ActividadesForm
from App.utils import crear_notificacion_sistema
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django import forms
from App.models import *

# Create your views here.

class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin para asegurar que solo usuarios autenticados con permisos
    de staff/administrador puedan acceder a las vistas administrativas.
    """
    def test_func(self):
        return self.request.user.is_active and self.request.user.is_staff

# ==========================================
# ACTIVIDADES
# ==========================================

class ActividadesListView(StaffRequiredMixin, ListView):
    model = Actividades
    template_name = 'actividades/actividades.html'
    context_object_name = 'actividades'

    def get_queryset(self):
        queryset = super().get_queryset()
        apto_menores_param = self.request.GET.get('apto_menores', '').strip().lower()
        if apto_menores_param == 'si':
            queryset = queryset.filter(apto_menores=True)
        elif apto_menores_param == 'no':
            queryset = queryset.filter(apto_menores=False)
        return queryset.order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stats = Actividades.objects.aggregate(
            total=Count('id'),
            activas=Count('id', filter=Q(estado=True)),
            inactivas=Count('id', filter=Q(estado=False))
        )
        context.update(stats)
        context['stats_list'] = [
            ('Total Actividades', stats['total'], 'text-dark'),
            ('Activas', stats['activas'], 'text-success'),
            ('Inactivas', stats['inactivas'], 'text-danger'),
        ]
        context['apto_menores_seleccionado'] = self.request.GET.get('apto_menores', '')
        return context


class ActividadesCreateView(StaffRequiredMixin, CreateView):
    model = Actividades
    form_class = ActividadesForm
    template_name = 'actividades/agregar_actividad.html'
    success_url = reverse_lazy('listar_actividades')

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
            accion="NUEVA ACTIVIDAD CREADA",
            tabla_afectada="Actividades",
            observacion=f"Se ha registrado con éxito la actividad: '{self.object.nombre}'.",
            valor_anterior="Ninguno (Registro Nuevo)",
            nuevo_valor=f"Nombre: {self.object.nombre}, Dificultad: {self.object.nivel_dificultad}"
        )
        return response


class ActividadesUpdateView(StaffRequiredMixin, UpdateView):
    model = Actividades
    form_class = ActividadesForm
    template_name = 'actividades/editar_actividad.html'
    success_url = reverse_lazy('listar_actividades')

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
        actividad_antigua = self.get_object()
        valor_viejo = f"Nombre: {actividad_antigua.nombre}, Dificultad: {actividad_antigua.nivel_dificultad}, Estado: {'Activa' if actividad_antigua.estado else 'Inactiva'}"

        response = super().form_valid(form)

        valor_nuevo = f"Nombre: {self.object.nombre}, Dificultad: {self.object.nivel_dificultad}, Estado: {'Activa' if self.object.estado else 'Inactiva'}"

        crear_notificacion_sistema(
            usuario=self.request.user,
            accion="ACTIVIDAD MODIFICADA",
            tabla_afectada="Actividades",
            observacion=f"La actividad '{self.object.nombre}' ha sido actualizada correctamente.",
            valor_anterior=valor_viejo,
            nuevo_valor=valor_nuevo
        )
        return response


class ActividadesDeleteView(StaffRequiredMixin, DeleteView):
    model = Actividades
    template_name = 'actividades/eliminar_actividad.html'
    success_url = reverse_lazy('listar_actividades')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Validar integridad: Prevenir eliminación si pertenece a paquetes activos
        if self.object.paquete_set.exists():
            messages.error(request, f"No se puede eliminar la actividad '{self.object.nombre}' porque está vinculada a uno o más paquetes.")
            return render(request, self.template_name, {'object': self.object})

        nombre_actividad = self.object.nombre
        valor_viejo = f"ID: {self.object.id}, Nombre: {self.object.nombre}, Dificultad: {self.object.nivel_dificultad}"

        response = super().delete(request, *args, **kwargs)

        crear_notificacion_sistema(
            usuario=request.user,
            accion="ACTIVIDAD ELIMINADA",
            tabla_afectada="Actividades",
            observacion=f"Se ha quitado del sistema la actividad: '{nombre_actividad}'.",
            valor_anterior=valor_viejo,
            nuevo_valor="Registro Eliminado"
        )
        return response