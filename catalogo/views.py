from django.urls import reverse_lazy
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Paquete, Actividades, Categoria, Tarifa, Temporada
from django.db.models import Count, Q
from django import forms
from notificaciones.utils import crear_notificacion_sistema

 

def destinos(request):
    """
    Vista que filtra y devuelve la lista de paquetes turísticos disponibles
    según los criterios de búsqueda (nombre, precio máximo, apto para menores y categoría).

    :param request: El objeto de la solicitud HTTP.
    :return: Una respuesta HTTP con la lista de destinos filtrados.
    """

    destinos_list = Paquete.objects.filter(estado=True)

    destinos_sugerencias = Paquete.objects.filter(estado=True).values('nombre').distinct()

    busqueda = request.GET.get('q', '').strip()
    precio_max = request.GET.get('precio_max')
    apto_menores = request.GET.get('apto_menores')
    categoria_id = request.GET.get('categoria')

    if busqueda:
        destinos_list = destinos_list.filter(nombre__icontains=busqueda)

    if precio_max:
        destinos_list = destinos_list.filter(
            tarifas__precio_adulto__lte=precio_max
        ).distinct()

    if apto_menores == 'si':
        destinos_list = destinos_list.exclude(actividades__apto_para_menores=False).distinct()
    elif apto_menores == 'no':
        destinos_list = destinos_list.exclude(actividades__apto_para_menores=True).distinct()

    if categoria_id:
        destinos_list = destinos_list.filter(categoria_id=categoria_id)

    # Carga optimizada en lote (evita N+1 consultas a la base de datos)
    destinos_list = destinos_list.select_related('categoria').prefetch_related('actividades', 'tarifas__temporada')
        
    categorias_list = Categoria.objects.all()

    context = {
        'destinos': destinos_list,                 
        'destinos_sugerencias': destinos_sugerencias,
        'categorias': categorias_list
    }
    return render(request, 'usuario/destinos.html', context)

# PAQUETES
class PaqueteListView(ListView):
    model = Paquete
    template_name = 'admin/paquetes/paquetes.html'
    context_object_name = 'paquetes'

    def get_queryset(self):
        """
        Filtra los paquetes según la categoría seleccionada en el formulario superior.
        """
        queryset = super().get_queryset()
        
        
        categoria_id = self.request.GET.get('categoria')
        
        if categoria_id:
            queryset = queryset.filter(categoria_id=categoria_id)
            
        return queryset.order_by('-id')

    def get_context_data(self, **kwargs):
        """
        Mantiene las estadísticas globales de paquetes e inyecta las categorías
        para renderizar el selector dinámico de filtros.
        """
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


class PaqueteCreateView(CreateView):
    model = Paquete
    fields = [
        'imagen', 'nombre', 'descripcion', 'hora_encuentro',
        'dias_duracion', 'noches_duracion', 'punto_encuentro', 'categoria', 'actividades'
    ]
    template_name = 'admin/paquetes/agregar_paquete.html'
    success_url = reverse_lazy('listar_paquetes')

    def get_form(self, form_class=None):
        """
        get_form.
        
        :param form_class=None: Crear un paquete turístico con el formulario especificado.
        
        :return: paquete turístico creado con éxito y notificación del sistema.
        """
        form = super().get_form(form_class)
        for name, field in form.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.Select) or isinstance(field.widget, forms.SelectMultiple):
                field.widget.attrs.update({'class': 'form-select'})
            else:
                field.widget.attrs.update({'class': 'form-control'})
        return form

    def form_valid(self, form):
        """
        form_valid.
        
        :param form: Descripción del parámetro.
        
        :return: Respuesta de la función.
        """
        response = super().form_valid(form)
        
        crear_notificacion_sistema(
            usuario=self.request.user,
            titulo=" Nuevo Paquete Creado",
            mensaje=f"Se ha creado con éxito el paquete turístico: '{self.object.nombre}'.",
            tipo='paquete'
        )
        return response
      

class PaqueteUpdateView(UpdateView):
    
    model = Paquete
    fields = [
        'imagen', 'nombre', 'descripcion', 'hora_encuentro',
        'dias_duracion', 'noches_duracion', 'punto_encuentro', 'categoria', 'actividades', 'estado'
    ]
    template_name = 'admin/paquetes/editar_paquete.html'
    success_url = reverse_lazy('listar_paquetes')

    def get_form(self, form_class=None):
        """
        get_form.
        
        :param form_class=None: editar un paquete turístico con el formulario especificado.
        
        :return: paquete turístico editado con éxito y notificación del sistema.
        """
        form = super().get_form(form_class)
        for name, field in form.fields.items():
            if isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-check-input'})
            elif isinstance(field.widget, forms.Select) or isinstance(field.widget, forms.SelectMultiple):
                field.widget.attrs.update({'class': 'form-select'})
            else:
                field.widget.attrs.update({'class': 'form-control'})
        return form
    def form_valid(self, form):
        response = super().form_valid(form)
    
        crear_notificacion_sistema(
            usuario=self.request.user,
            titulo=" Paquete Actualizado",
            mensaje=f"El paquete '{self.object.nombre}' ha sido modificado correctamente.",
            tipo='paquete'
        )
        return response


class PaqueteDeleteView(DeleteView):
    model = Paquete
    template_name = 'admin/paquetes/eliminar_paquete.html'
    success_url = reverse_lazy('listar_paquetes')
    
    def delete(self, request, *args, **kwargs):
        """
        delete.
        
        :param request: borrar un paquete turístico con la solicitud especificada.
        
        :param args: parametros adicionales para la solicitud de eliminación.
        
        :param kwargs: parametros adicionales para la solicitud de eliminación.
        
        :return: paquete turístico eliminado con éxito y notificación del sistema.
        """
        self.object = self.get_object()
        nombre_paquete = self.object.nombre 
        response = super().delete(request, *args, **kwargs)
        
    
        crear_notificacion_sistema(
            usuario=request.user,
            titulo=" Paquete Eliminado",
            mensaje=f"Se ha eliminado del sistema el paquete: '{nombre_paquete}'.",
            tipo='paquete'
        )
        return response

# ACTIVIDADES

class ActividadesListView(ListView):
    model = Actividades
    template_name = 'admin/actividades/actividades.html'
    context_object_name = 'actividades'
       
    def get_queryset(self):
        """
        Filtra el set de datos principal antes de mandarlo al template.
        """
        queryset = super().get_queryset()
        
   
        apto_menores_param = self.request.GET.get('apto_menores')
        
        if apto_menores_param == 'si':
            queryset = queryset.filter(apto_para_menores=True)
        elif apto_menores_param == 'no':
            queryset = queryset.filter(apto_para_menores=False)
            
        return queryset.order_by('-id')

    def get_context_data(self, **kwargs):
        """
        Mantiene el conteo global de estadísticas intacto y pasa el estado actual del filtro.
        """
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


class ActividadesCreateView(CreateView):
    model = Actividades
    fields = ['nombre', 'descripcion', 'nivel_dificultad', 'equipo_requerimiento',
              'recomendacion_salud', 'apto_para_menores']
    template_name = 'admin/actividades/agregar_actividad.html'
    success_url = reverse_lazy('listar_actividades')

    def get_form(self, form_class=None):
        """
        get_form.
        
        :param form_class=None: Crear una actividad con el formulario especificado.
        
        :return: actividad creada con éxito y notificación del sistema.
        """
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
        """
        form_valid.
        
        :param form: Descripción del parámetro.
        
        :return: Respuesta de la función.
        """
        response = super().form_valid(form)
        crear_notificacion_sistema(
            usuario=self.request.user,
            titulo=" Nueva Actividad Creada",
            mensaje=f"Se ha registrado con éxito la actividad: '{self.object.nombre}'.",
            tipo='sistema'  
        )
        return response


class ActividadesUpdateView(UpdateView):
    model = Actividades
    fields = ['nombre', 'descripcion', 'nivel_dificultad', 'equipo_requerimiento',
              'recomendacion_salud', 'estado', 'apto_para_menores']
    template_name = 'admin/actividades/editar_actividad.html'
    success_url = reverse_lazy('listar_actividades')

    def get_form(self, form_class=None):
        """
        get_form.
        
        :param form_class=None: Editar una actividad con el formulario especificado.    
        
        :return: actividad editada con éxito y notificación del sistema.
        """
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
        """
        form_valid.
        
        :param form: Descripción del parámetro.
        
        :return: Editar una actividad con éxito y notificación del sistema.
        """
        response = super().form_valid(form)
        crear_notificacion_sistema(
            usuario=self.request.user,
            titulo=" Actividad Modificada",
            mensaje=f"La actividad '{self.object.nombre}' ha sido actualizada correctamente.",
            tipo='sistema'
        )
        return response


class ActividadesDeleteView(DeleteView):
    model = Actividades
    template_name = 'admin/actividades/eliminar_actividad.html'
    success_url = reverse_lazy('listar_actividades')
    
    def delete(self, request, *args, **kwargs):
        """
        delete.
        
        :param request: borrar una actividad con la solicitud especificada.
        
        :param args: parametros adicionales para la solicitud de eliminación.
        
        :param kwargs: parametros adicionales para la solicitud de eliminación.
        
        :return: actividad eliminada con éxito y notificación del sistema.
        """
        self.object = self.get_object()
        nombre_actividad = self.object.nombre  
        response = super().delete(request, *args, **kwargs)
        
        crear_notificacion_sistema(
            usuario=request.user,
            titulo=" Actividad Eliminada",
            mensaje=f"Se ha quitado del sistema la actividad: '{nombre_actividad}'.",
            tipo='sistema'
        )
        return response


class CategoriaListView(ListView):
    model = Categoria
    template_name = 'admin/categorias/categorias.html'
    context_object_name = 'categorias'
    
    def get_queryset(self):
        return super().get_queryset().order_by('-id')


    def get_context_data(self, **kwargs):
        """
        get_context_data.
        
        :param kwargs: La lista de las categorías y otros argumentos de contexto.
        
        :return: lista de categorías y estadísticas de las categorías.
        """
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


class CategoriaCreateView(CreateView):
    model = Categoria
    fields = ['nombre', 'descripcion']
    template_name = 'admin/categorias/agregar_categoria.html'
    success_url = reverse_lazy('listar_categorias')

    def get_form(self, form_class=None):
        """
        get_form.
        
        :param form_class=None: Crear una categoría con el formulario especificado.
        
        :return: categoría creada con éxito y notificación del sistema.
        """
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
        """
        form_valid.
        
        :param form: crear una categoría con el formulario especificado.
        
        :return: exito al crear una categoría y notificación del sistema.
        """
        response = super().form_valid(form)
        crear_notificacion_sistema(
            usuario=self.request.user,
            titulo="📁 Nueva Categoría Creada",
            mensaje=f"Se ha registrado con éxito la categoría: '{self.object.nombre}'.",
            tipo='sistema'
        )
        return response
    
    

class CategoriaUpdateView(UpdateView):
    model = Categoria
    fields = ['nombre', 'descripcion', 'estado']
    template_name = 'admin/categorias/editar_categoria.html'
    success_url = reverse_lazy('listar_categorias')

    def get_form(self, form_class=None):
        """
        get_form.
        
        :param form_class=None: Editar una categoría con el formulario especificado.
        
        :return: categoría editada con éxito y notificación del sistema.
        """
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
        """
        form_valid.
        
        :param form: Editar una categoría con el formulario especificado.
        
        :return: categoría editada con éxito y notificación del sistema.
        """
        response = super().form_valid(form)
        crear_notificacion_sistema(
            usuario=self.request.user,
            titulo=" Categoría Modificada",
            mensaje=f"La categoría '{self.object.nombre}' ha sido actualizada correctamente.",
            tipo='sistema'
        )
        return response


class CategoriaDeleteView(DeleteView):
    model = Categoria
    template_name = 'admin/categorias/eliminar_categoria.html'
    success_url = reverse_lazy('listar_categorias')
    
    def delete(self, request, *args, **kwargs):
        """
        delete.
        
        :param request: categoría a eliminar con la solicitud especificada.
        
        :param args: parametros adicionales para la solicitud de eliminación.
        
        :param kwargs: parametros adicionales para la solicitud de eliminación.
        
        :return: categoría eliminada con éxito y notificación del sistema.
        """
        self.object = self.get_object()
        nombre_categoria = self.object.nombre  
        response = super().delete(request, *args, **kwargs)
        
        crear_notificacion_sistema(
            usuario=request.user,
            titulo=" Categoría Eliminada",
            mensaje=f"Se ha quitado del sistema la categoría: '{nombre_categoria}'.",
            tipo='sistema'
        )
        return response


def reservas(request):
    """
    reservas.
    
    :param request: reservas de los paquetes turísticos según la solicitud especificada.
    
    :return: reservas de los paquetes turísticos y notificación del sistema.
    """

    context = {
        'reservas': []  # Reemplaza con la lógica real
    }
    return render(request, 'usuario/reservas.html', context)

# TARIFAS

class TarifaListView(ListView):
    model = Tarifa
    template_name = 'admin/tarifas/tarifas.html'
    context_object_name = 'tarifas'

    def get_queryset(self):
        """
        Filtra las tarifas en base al paquete turístico seleccionado.
        """
        queryset = super().get_queryset()
        
       
        paquete_id = self.request.GET.get('paquete')
        
        if paquete_id:
            queryset = queryset.filter(paquete_id=paquete_id)
            
        return queryset.order_by('-id')

    def get_context_data(self, **kwargs):
        """
        Mantiene las estadísticas globales e inyecta la lista de paquetes para el filtro.
        """
        context = super().get_context_data(**kwargs)

     
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
        
        
        context['paquetes'] = Paquete.objects.all()
        
      
        context['paquete_seleccionado'] = self.request.GET.get('paquete', '')
        
        return context


class TarifaCreateView(CreateView):
    model = Tarifa
    fields = ['paquete', 'temporada', 'precio_adulto', 'precio_menor']
    template_name = 'admin/tarifas/agregar_tarifa.html'
    success_url = reverse_lazy('listar_tarifas')
    
    def form_valid(self, form):
        """
        form_valid.
        
        :param form: crear una tarifa con el formulario especificado.
        
        :return: crear una tarifa con éxito y notificación del sistema.
        """
        response = super().form_valid(form)
        crear_notificacion_sistema(
            usuario=self.request.user,
            titulo=" Nueva Tarifa Creada",
            mensaje=f"Se ha registrado con éxito una nueva tarifa en el sistema.",
            tipo='sistema'
        )
        return response
    
    


class TarifaUpdateView(UpdateView):
    model = Tarifa
    fields = ['paquete', 'temporada', 'precio_adulto', 'precio_menor','estado']
    template_name = 'admin/tarifas/editar_tarifa.html'
    success_url = reverse_lazy('listar_tarifas')
    
    def form_valid(self, form):
        """
        form_valid.
        
        :param form: editar una tarifa con el formulario especificado.
        
        :return: editar una tarifa con éxito y notificación del sistema.
        """
        response = super().form_valid(form)
        crear_notificacion_sistema(
            usuario=self.request.user,
            titulo="✏️ Tarifa Modificada",
            mensaje=f"Los datos de la tarifa han sido actualizados correctamente.",
            tipo='sistema'
        )
        return response



class TemporadaListView(ListView):
    model = Temporada
    template_name = 'admin/temporada/temporada.html'
    context_object_name = 'temporadas'

    def get_queryset(self):
        queryset = Temporada.objects.all()

        fecha_inicio = self.request.GET.get("fecha_inicio")
        fecha_fin = self.request.GET.get("fecha_fin")

        if fecha_inicio:
            queryset = queryset.filter(fecha_inicio__gte=fecha_inicio)

        if fecha_fin:
            queryset = queryset.filter(fecha_fin__lte=fecha_fin)

        return queryset.order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

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
    fields = ['nombre', 'fecha_inicio', 'fecha_fin']
    template_name = 'admin/temporada/agregar_temporada.html'
    success_url = reverse_lazy('listar_temporadas')
    
    def form_valid(self, form):
        """
        form_valid.
        
        :param form: crear una temporada con el formulario especificado.
        
        :return: temporada creada con éxito y notificación del sistema.
        """
        response = super().form_valid(form)
        crear_notificacion_sistema(
            usuario=self.request.user,
            titulo=" Nueva Temporada Creada",
            mensaje=f"Se ha registrado con éxito la temporada: '{self.object.nombre}'.",
            tipo='sistema'
        )
        return response


class TemporadaUpdateView(UpdateView):
    model = Temporada
    fields = ['nombre', 'fecha_inicio', 'fecha_fin','estado']
    template_name = 'admin/temporada/editar_temporada.html'
    success_url = reverse_lazy('listar_temporadas')
    
    def form_valid(self, form):
        """
        form_valid.
        
        :param form: crear una temporada con el formulario especificado.
        
        :return: temporada editada con éxito y notificación del sistema.
        """
        response = super().form_valid(form)
        crear_notificacion_sistema(
            usuario=self.request.user,
            titulo=" Temporada Modificada",
            mensaje=f"La temporada '{self.object.nombre}' ha sido actualizada correctamente.",
            tipo='sistema'
        )
        return response
