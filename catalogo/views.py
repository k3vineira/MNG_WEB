from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Paquete, Actividades, Categoria



def destinos(request):
    destinos_list = Paquete.objects.all()

    # Captura de datos del buscador
    busqueda = request.GET.get('q', '').strip()
    precio_max = request.GET.get('precio_max')

    if busqueda:
        destinos_list = destinos_list.filter(nombre__icontains=busqueda)

    if precio_max:
        destinos_list = destinos_list.filter(precio__lte=precio_max)
    
    return render(request, 'usuario/destinos.html', {'destinos': destinos_list})


class PaqueteListView(ListView):
    model = Paquete
    template_name = 'admin/paquetes/paquetes.html' 
    context_object_name = 'paquetes'

class PaqueteCreateView(CreateView):
    model = Paquete
    fields = [
        'imagen', 'nombre', 'descripcion', 'precio', 
        'duracion_estimada', 'punto_encuentro', 'codigo_categoria', 'actividades'
    ]
    template_name = 'admin/paquetes/agregar_paquete.html'
    success_url = reverse_lazy('listar_paquetes') 


class PaqueteUpdateView(UpdateView):
    model = Paquete
    fields = [
        'imagen', 'nombre', 'descripcion', 'precio', 
        'duracion_estimada', 'punto_encuentro', 'codigo_categoria', 'actividades'
    ]
    template_name = 'admin/paquetes/editar_paquete.html'
    success_url = reverse_lazy('listar_paquetes')


class PaqueteDeleteView(DeleteView):
    model = Paquete
    template_name = 'admin/paquetes/eliminar_paquete.html'
    success_url = reverse_lazy('listar_paquetes')

#ACTIVIDADES

class ActividadesListView(ListView):
    model = Actividades
    template_name = 'admin/actividades/actividades.html' 
    context_object_name = 'actividades'

class ActividadesCreateView(CreateView):
    model = Actividades
    fields = ['nombre', 'descripcion', 'nivel_dificultad', 'equipo_requerimiento', 'recomendacion_salud']
    template_name = 'admin/actividades/agregar_actividad.html'
    success_url = reverse_lazy('listar_actividades')

class ActividadesUpdateView(UpdateView):
    model = Actividades
    fields = ['nombre', 'descripcion', 'nivel_dificultad', 'equipo_requerimiento', 'recomendacion_salud']
    template_name = 'admin/actividades/editar_actividad.html'
    success_url = reverse_lazy('listar_actividades')

class ActividadesDeleteView(DeleteView):
    model = Actividades
    template_name = 'admin/actividades/eliminar_actividad.html'
    success_url = reverse_lazy('listar_actividades')

#CATEGORIAS
class CategoriaListView(ListView):
    model = Categoria
    template_name = 'admin/categorias/categorias.html' 
    context_object_name = 'categorias'

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

class CategoriaDeleteView(DeleteView):
    model = Categoria
    template_name = 'admin/categorias/eliminar_categoria.html'
    success_url = reverse_lazy('listar_categorias')
