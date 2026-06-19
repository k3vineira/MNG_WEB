from django.urls import reverse_lazy
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Paquete, Actividades, Categoria, Tarifa, Temporada
from django.db.models import Count, Q
from django import forms
from .forms import TemporadaForm, TarifaForm


def destinos(request):
    destinos_list = Paquete.objects.filter(estado=True)
    busqueda = request.GET.get('q', '').strip()
    precio_max = request.GET.get('precio_max')
    apto_menores = request.GET.get('apto_menores')
    categoria_id = request.GET.get('categoria')

    if busqueda:
        destinos_list = destinos_list.filter(nombre__icontains=busqueda)

    if precio_max:
        destinos_list = destinos_list.filter(
            tarifas__precio_adulto__lte=precio_max).distinct()

    if apto_menores == 'si':
        destinos_list = destinos_list.filter(
            actividades__apto_para_menores=True).distinct()
    elif apto_menores == 'no':
        destinos_list = destinos_list.filter(
            actividades__apto_para_menores=False).distinct()

    if categoria_id:
        destinos_list = destinos_list.filter(categoria_id=categoria_id)
    categorias_list = Categoria.objects.all()

    context = {
        'destinos': destinos_list,
        'categorias': categorias_list
    }
    return render(request, 'usuario/destinos.html', context)


# PAQUETES
class PaqueteListView(ListView):
    model = Paquete
    template_name = 'admin/paquetes/paquetes.html'
    context_object_name = 'paquetes'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Conteo para los paquetes
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
        return context


class PaqueteCreateView(CreateView):
    model = Paquete
    fields = [
        'imagen', 'nombre', 'descripcion', 'hora_encuentro',
        'dias_duracion', 'noches_duracion', 'punto_encuentro', 'categoria', 'actividades', 'estado'
    ]
    template_name = 'admin/paquetes/agregar_paquete.html'
    success_url = reverse_lazy('listar_paquetes')


class PaqueteUpdateView(UpdateView):
    model = Paquete
    fields = [
        'imagen', 'nombre', 'descripcion', 'hora_encuentro',
        'dias_duracion', 'noches_duracion', 'punto_encuentro', 'categoria', 'actividades', 'estado'
    ]
    template_name = 'admin/paquetes/editar_paquete.html'
    success_url = reverse_lazy('listar_paquetes')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-control'})
        return form


class PaqueteDeleteView(DeleteView):
    model = Paquete
    template_name = 'admin/paquetes/eliminar_paquete.html'
    success_url = reverse_lazy('listar_paquetes')

# ACTIVIDADES


class ActividadesListView(ListView):
    model = Actividades
    template_name = 'admin/actividades/actividades.html'
    context_object_name = 'actividades'

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
        return context


class ActividadesCreateView(CreateView):
    model = Actividades
    fields = ['nombre', 'descripcion', 'nivel_dificultad', 'equipo_requerimiento',
              'recomendacion_salud', 'estado', 'apto_para_menores']
    template_name = 'admin/actividades/agregar_actividad.html'
    success_url = reverse_lazy('listar_actividades')


class ActividadesUpdateView(UpdateView):
    model = Actividades
    fields = ['nombre', 'descripcion', 'nivel_dificultad', 'equipo_requerimiento',
              'recomendacion_salud', 'estado', 'apto_para_menores']
    template_name = 'admin/actividades/editar_actividad.html'
    success_url = reverse_lazy('listar_actividades')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            else:

                field.widget.attrs.update({'class': 'form-control'})
        return form


class ActividadesDeleteView(DeleteView):
    model = Actividades
    template_name = 'admin/actividades/eliminar_actividad.html'
    success_url = reverse_lazy('listar_actividades')


class CategoriaListView(ListView):
    model = Categoria
    template_name = 'admin/categorias/categorias.html'
    context_object_name = 'categorias'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # 2. Realizamos el cálculo
        stats = Categoria.objects.aggregate(
            total=Count('id'),
            activas=Count('id', filter=Q(estado=True)),
            inactivas=Count('id', filter=Q(estado=False))
        )

        # 3. Agregamos stats_list al contexto
        context['stats_list'] = [
            ('Total Categorías', stats['total'], 'text-dark'),
            ('Activas', stats['activas'], 'text-success'),
            ('Inactivas', stats['inactivas'], 'text-danger'),
        ]

        return context


class CategoriaCreateView(CreateView):
    model = Categoria
    fields = ['nombre', 'descripcion', 'estado']
    template_name = 'admin/categorias/agregar_categoria.html'
    success_url = reverse_lazy('listar_categorias')


class CategoriaUpdateView(UpdateView):
    model = Categoria
    fields = ['nombre', 'descripcion', 'estado']
    template_name = 'admin/categorias/editar_categoria.html'
    success_url = reverse_lazy('listar_categorias')

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        for field in form.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-control'})
        return form


class CategoriaDeleteView(DeleteView):
    model = Categoria
    template_name = 'admin/categorias/eliminar_categoria.html'
    success_url = reverse_lazy('listar_categorias')


def reservas(request):

    context = {
        'reservas': []  # Reemplaza con la lógica real
    }
    return render(request, 'usuario/reservas.html', context)

# TARIFAS


class TarifaListView(ListView):
    model = Tarifa
    template_name = 'admin/tarifas/tarifas.html'
    context_object_name = 'tarifas'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Contamos estados de tarifas
        stats = Tarifa.objects.aggregate(
            total=Count('id'),
            activas=Count('id', filter=Q(estado='activa')),
            inactivas=Count('id', filter=Q(estado='inactiva'))
        )

        context.update(stats)
        context['stats_list'] = [
            ('Total', stats['total'], 'text-dark'),
            ('Activas', stats['activas'], 'text-success'),
            ('Inactivas', stats['inactivas'], 'text-danger'),
        ]
        return context


class TarifaCreateView(CreateView):
    model = Tarifa
    form_class = TarifaForm
    template_name = 'admin/tarifas/agregar_tarifa.html'
    success_url = reverse_lazy('listar_tarifas')


class TarifaUpdateView(UpdateView):
    model = Tarifa
    form_class = TarifaForm
    template_name = 'admin/tarifas/editar_tarifa.html'
    success_url = reverse_lazy('listar_tarifas')


# temporada
class TemporadaListView(ListView):
    model = Temporada
    template_name = 'admin/temporada/temporada.html'
    context_object_name = 'temporadas'

    def get_context_data(self, **kwargs):
        # Esta línea debe tener 8 espacios de indentación
        context = super().get_context_data(**kwargs)

        # Contamos estados de temporadas
        stats = Temporada.objects.aggregate(
            total=Count('id'),
            programadas=Count('id', filter=Q(estado='programada')),
            activas=Count('id', filter=Q(estado='activa')),
            finalizadas=Count('id', filter=Q(estado='finalizada'))
        )

        context.update(stats)
        context['stats_list'] = [
            ('Total', stats['total'], 'text-dark'),
            ('Programadas', stats['programadas'], 'text-secondary'),
            ('Activas', stats['activas'], 'text-success'),
            ('Finalizadas', stats['finalizadas'], 'text-info'),
        ]
        return context


class TemporadaCreateView(CreateView):
    model = Temporada
    form_class = TemporadaForm
    template_name = 'admin/temporada/agregar_temporada.html'
    success_url = reverse_lazy('listar_temporadas')


class TemporadaUpdateView(UpdateView):
    model = Temporada
    form_class = TemporadaForm
    template_name = 'admin/temporada/editar_temporada.html'
    success_url = reverse_lazy('listar_temporadas')
