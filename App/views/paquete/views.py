from django.shortcuts import render
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Count, Q
from django.contrib import messages
from App.forms.paquete.forms import PaqueteForm
from App.utils import crear_notificacion_sistema
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django import forms
from App.models import Paquete, Categoria, Actividades, Tarifa, Temporada
from decimal import Decimal, InvalidOperation


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin para asegurar que solo usuarios autenticados con permisos
    de staff/administrador puedan acceder a las vistas administrativas.
    """
    def test_func(self):
        return self.request.user.is_active and self.request.user.is_staff

def tours(request):
    """
    Vista pública que filtra y devuelve el catálogo de tours y paquetes turísticos disponibles.
    Aplica sanitización y validaciones exhaustivas a los parámetros de búsqueda y filtrado GET.
    """
    lista_tours = Paquete.objects.filter(estado=True)
    sugerencias_tours = Paquete.objects.filter(estado=True).values('nombre').distinct()

    # 1. Filtro de búsqueda textual por nombre del tour
    busqueda = request.GET.get('q', '').strip()
    if busqueda and len(busqueda) <= 100:
        lista_tours = lista_tours.filter(nombre__icontains=busqueda)

    # 2. Filtro de precio máximo permitido
    precio_max = request.GET.get('precio_max', '').strip()
    if precio_max:
        try:
            precio_decimal = Decimal(precio_max)
            if precio_decimal >= 0:
                lista_tours = lista_tours.filter(
                    tarifas__precio_adulto__lte=precio_decimal
                ).distinct()
        except (InvalidOperation, TypeError):
            pass

    # 3. Filtro según aptitud para menores de edad
    apto_menores = request.GET.get('apto_menores', '').strip().lower()
    if apto_menores == 'si':
        lista_tours = lista_tours.exclude(actividades__apto_menores=False).distinct()
    elif apto_menores == 'no':
        lista_tours = lista_tours.exclude(actividades__apto_menores=True).distinct()

    # 4. Filtro por categoría del tour
    categoria_id = request.GET.get('categoria', '').strip()
    if categoria_id:
        try:
            cat_id = int(categoria_id)
            if cat_id > 0:
                lista_tours = lista_tours.filter(categoria_id=cat_id)
        except (ValueError, TypeError):
            pass

    lista_tours = lista_tours.select_related('categoria').prefetch_related('actividades', 'tarifas__temporada')
    lista_categorias = Categoria.objects.filter(estado=True)

    contexto = {
        'tours': lista_tours,
        'sugerencias_tours': sugerencias_tours,
        'categorias': lista_categorias,
    }
    return render(request, 'admin/paquete/destinos.html', contexto)


# ==========================================
# PAQUETES (ADMINISTRACIÓN)
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
            messages.error(request, f"No se puede eliminar el paquete '{self.object.nombre}' porque tiene tarifas asociadas. Elimina las tarifas primero.")
            return render(request, self.template_name, {'object': self.object, 'paquete': self.object})

        if hasattr(self.object, 'reservas') and self.object.reservas.exists():
            messages.error(request, f"No se puede eliminar el paquete '{self.object.nombre}' porque tiene reservas vinculadas.")
            return render(request, self.template_name, {'object': self.object, 'paquete': self.object})

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


