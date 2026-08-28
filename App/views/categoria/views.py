from django.urls import reverse_lazy
from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteViewr
from django.contrib import messages
from django import forms
from django.db.models import Count, Q
from App.forms.categoria.forms import CategoriaForm
from App.models import*
from App.mixins import StaffRequiredMixin
from App.utils import crear_notificacion_sistema
from django.views.generic.edit import DeleteView



# Create your views here.

class CategoriaListView(StaffRequiredMixin, ListView):
    model = Categoria
    template_name = 'admin/categorias/categorias.html'
    context_object_name = 'categorias'

    def get_queryset(self):
        return super().get_queryset().order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stats = Categoria.objects.aggregate(
            total=Count('id'),
            activas=Count('id', filter=Q(estado=True)),
            inactivas=Count('id', filter=Q(estado=False))
        )
        context['stats_list'] = [
            ('Total Categorías', stats['total'], 'text-dark'),
            ('Activas', stats['activas'], 'text-success'),
            ('Inactivas', stats['inactivas'], 'text-danger'),
        ]
        return context


class CategoriaCreateView(StaffRequiredMixin, CreateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'admin/categorias/agregar_categoria.html'
    success_url = reverse_lazy('listar_categorias')

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
            accion="NUEVA CATEGORIA CREADA",
            tabla_afectada="Categorías",
            observacion=f"Se ha registrado con éxito la categoría: '{self.object.nombre}'.",
            valor_anterior="Ninguno (Registro Nuevo)",
            nuevo_valor=f"Nombre: {self.object.nombre}"
        )
        return response


class CategoriaUpdateView(StaffRequiredMixin, UpdateView):
    model = Categoria
    form_class = CategoriaForm
    template_name = 'admin/categorias/editar_categoria.html'
    success_url = reverse_lazy('listar_categorias')

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
        cat_antigua = self.get_object()
        valor_viejo = f"Nombre: {cat_antigua.nombre}, Descripción: {cat_antigua.descripcion}"

        response = super().form_valid(form)

        valor_nuevo = f"Nombre: {self.object.nombre}, Descripción: {self.object.descripcion}"

        crear_notificacion_sistema(
            usuario=self.request.user,
            accion="CATEGORIA MODIFICADA",
            tabla_afectada="Categorías",
            observacion=f"La categoría '{self.object.nombre}' ha sido actualizada correctamente.",
            valor_anterior=valor_viejo,
            nuevo_valor=valor_nuevo
        )
        return response


class CategoriaDeleteView(StaffRequiredMixin, DeleteView):
    model = Categoria
    template_name = 'admin/categorias/eliminar_categoria.html'
    success_url = reverse_lazy('listar_categorias')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()

        # Validar integridad: No eliminar categoría si está asignada a algún paquete
        if self.object.paquete_set.exists():
            messages.error(request, f"No se puede eliminar la categoría '{self.object.nombre}' porque contiene paquetes asociados.")
            return render(request, self.template_name, {'object': self.object})

        nombre_categoria = self.object.nombre
        valor_viejo = f"ID: {self.object.id}, Nombre: {self.object.nombre}"

        response = super().delete(request, *args, **kwargs)

        crear_notificacion_sistema(
            usuario=request.user,
            accion="CATEGORIA ELIMINADA",
            tabla_afectada="Categorías",
            observacion=f"Se ha quitado del sistema la categoría: '{nombre_categoria}'.",
            valor_anterior=valor_viejo,
            nuevo_valor="Registro Eliminado"
        )
        return response

