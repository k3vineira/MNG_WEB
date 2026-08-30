from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.contrib import messages
from App.forms.paquete.forms import PaqueteForm
from App.utils import crear_notificacion_sistema
from App.mixins import StaffRequiredMixin
from django import forms
from App.models import *
from decimal import Decimal, InvalidOperation


# Create your views here.
def destinos(request):
    """
    Vista pública que filtra y devuelve la lista de paquetes turísticos disponibles.
    Incluye validaciones y sanitización para los parámetros GET.
    """
    destinos_list = Paquete.objects.filter(estado=True)
    destinos_sugerencias = Paquete.objects.filter(estado=True).values('nombre').distinct()

    # Validar y sanitizar búsqueda textual
    busqueda = request.GET.get('q', '').strip()
    if busqueda and len(busqueda) <= 100:
        destinos_list = destinos_list.filter(nombre__icontains=busqueda)

    # Validar que precio_max sea un decimal/entero positivo válido
    precio_max = request.GET.get('precio_max', '').strip()
    if precio_max:
        try:
            precio_decimal = Decimal(precio_max)
            if precio_decimal >= 0:
                destinos_list = destinos_list.filter(
                    tarifas__precio_adulto__lte=precio_decimal
                ).distinct()
        except (InvalidOperation, TypeError):
            pass  # Ignorar filtro si envían un valor no numérico o malicioso

    # Validar parámetro estricto de apto_menores
    apto_menores = request.GET.get('apto_menores', '').strip().lower()
    if apto_menores == 'si':
        destinos_list = destinos_list.exclude(actividades__apto_menores=False).distinct()
    elif apto_menores == 'no':
        destinos_list = destinos_list.exclude(actividades__apto_menores=True).distinct()

    # Validar que categoria_id sea un entero válido
    categoria_id = request.GET.get('categoria', '').strip()
    if categoria_id:
        try:
            cat_id = int(categoria_id)
            if cat_id > 0:
                destinos_list = destinos_list.filter(categoria_id=cat_id)
        except (ValueError, TypeError):
            pass

    # Carga optimizada
    destinos_list = destinos_list.select_related('categoria').prefetch_related('actividades', 'tarifas__temporada')
    categorias_list = Categoria.objects.filter(estado=True)

    context = {
        'destinos': destinos_list,
        'destinos_sugerencias': destinos_sugerencias,
        'categorias': categorias_list
    }
    return render(request, 'usuario/destinos.html', context)



# ==========================================
# PAQUETES
# ==========================================

class PaqueteListView(StaffRequiredMixin, ListView):
    model = Paquete
    template_name = 'admin/paquete/paquetes.html'
    context_object_name = 'paquetes'

    def get_queryset(self):
        queryset = super().get_queryset().select_related('categoria').prefetch_related('actividades', 'tarifas')
        categoria_id = self.request.GET.get('categoria', '').strip()
        if categoria_id:
            try:
                cat_id = int(categoria_id)
                if cat_id > 0:
                    queryset = queryset.filter(categoria_id=cat_id)
            except (ValueError, TypeError):
                pass
        return queryset.order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stats = Paquete.objects.aggregate(
            total=Count('id'),
            activos=Count('id', filter=Q(estado=True)),
            inactivos=Count('id', filter=Q(estado=False))
        )
        context.update(stats)
        context['stats_list'] = [
            ('Total Paquetes', stats['total'], 'text-dark'),
            ('Activos', stats['activos'], 'text-success'),
            ('Inactivos', stats['inactivos'], 'text-danger'),
        ]
        context['categorias'] = Categoria.objects.all()
        context['categoria_seleccionada'] = self.request.GET.get('categoria', '')
        return context


class PaqueteCreateView(StaffRequiredMixin, CreateView):
    model = Paquete
    form_class = PaqueteForm
    template_name = 'admin/paquete/agregar_paquete.html'
    success_url = reverse_lazy('listar_paquetes')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for name, field in form.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs.update({'class': 'form-select'})
            else:
                field.widget.attrs.update({'class': 'form-control'})
        return form

    def form_valid(self, form):
        response = super().form_valid(form)
        crear_notificacion_sistema(
            usuario=self.request.user,
            accion="NUEVO PAQUETE CREADO",
            tabla_afectada="Paquetes",
            observacion=f"Se ha creado con éxito el paquete turístico: '{self.object.nombre}'.",
            valor_anterior="Ninguno (Registro Nuevo)",
            nuevo_valor=f"Nombre: {self.object.nombre}, Categoría: {self.object.categoria}"
        )
        return response


class PaqueteUpdateView(StaffRequiredMixin, UpdateView):
    model = Paquete
    form_class = PaqueteForm
    template_name = 'admin/paquete/editar_paquete.html'
    success_url = reverse_lazy('listar_paquetes')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for name, field in form.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, (forms.Select, forms.SelectMultiple)):
                field.widget.attrs.update({'class': 'form-select'})
            else:
                field.widget.attrs.update({'class': 'form-control'})
        return form

    def form_valid(self, form):
        paquete_antiguo = self.get_object()
        valor_viejo = f"Nombre: {paquete_antiguo.nombre}, Categoría: {paquete_antiguo.categoria}, Estado: {'Activo' if paquete_antiguo.estado else 'Inactivo'}"

        response = super().form_valid(form)

        valor_nuevo = f"Nombre: {self.object.nombre}, Categoría: {self.object.categoria}, Estado: {'Activo' if self.object.estado else 'Inactivo'}"

        crear_notificacion_sistema(
            usuario=self.request.user,
            accion="PAQUETE MODIFICADO",
            tabla_afectada="Paquetes",
            observacion=f"El paquete '{self.object.nombre}' ha sido modificado correctamente.",
            valor_anterior=valor_viejo,
            nuevo_valor=valor_nuevo
        )
        return response


class PaqueteDeleteView(StaffRequiredMixin, DeleteView):
    model = Paquete
    template_name = 'admin/paquete/eliminar_paquete.html'
    success_url = reverse_lazy('listar_paquetes')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        
        # Validar integridad referencial: Prevenir borrado si el paquete tiene tarifas asociadas
        if self.object.tarifas.exists():
            messages.error(request, f"No se puede eliminar el paquete '{self.object.nombre}' porque tiene tarifas registradas.")
            return render(request, self.template_name, {'object': self.object})

        nombre_paquete = self.object.nombre
        valor_viejo = f"ID: {self.object.id}, Nombre: {self.object.nombre}, Categoría: {self.object.categoria}"
        
        response = super().delete(request, *args, **kwargs)

        crear_notificacion_sistema(
            usuario=request.user,
            accion="PAQUETE ELIMINADO",
            tabla_afectada="Paquetes",
            observacion=f"Se ha eliminado del sistema el paquete: '{nombre_paquete}'.",
            valor_anterior=valor_viejo,
            nuevo_valor="Registro Eliminado"
        )
        return response

