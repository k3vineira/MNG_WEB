from django.urls import reverse_lazy
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from .models import Paquete, Actividades, Categoria, Tarifa ,Temporada



def destinos(request):
    destinos_list = Paquete.objects.filter(estado=True)

    busqueda = request.GET.get('q', '').strip()
    precio_max = request.GET.get('precio_max')
    apto_menores = request.GET.get('apto_menores') # <--- Capturamos el nuevo filtro

    if busqueda:
        destinos_list = destinos_list.filter(nombre__icontains=busqueda)

    if precio_max:
        destinos_list = destinos_list.filter(tarifas__precio_adulto__lte=precio_max).distinct()
    
    if apto_menores == 'si':
     
        destinos_list = destinos_list.filter(actividades__apto_para_menores=True).distinct()
    elif apto_menores == 'no':
        
        destinos_list = destinos_list.filter(actividades__apto_para_menores=False).distinct()
        
    return render(request, 'usuario/destinos.html', {'destinos': destinos_list})



#PAQUETES
class PaqueteListView(ListView):
    model = Paquete
    template_name = 'admin/paquetes/paquetes.html' 
    context_object_name = 'paquetes'

class PaqueteCreateView(CreateView):
    model = Paquete
    fields = [
        'imagen', 'nombre', 'descripcion', 
        'dias_duracion', 'noches_duracion', 'punto_encuentro', 'categoria', 'actividades','estado'
    ]
    template_name = 'admin/paquetes/agregar_paquete.html'
    success_url = reverse_lazy('listar_paquetes') 


class PaqueteUpdateView(UpdateView):
    model = Paquete
    fields = [
        'imagen', 'nombre', 'descripcion', 
        'dias_duracion', 'noches_duracion', 'punto_encuentro', 'categoria', 'actividades','estado'
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
    fields = ['nombre', 'descripcion', 'nivel_dificultad', 'equipo_requerimiento', 'recomendacion_salud', 'estado', 'apto_para_menores']
    template_name = 'admin/actividades/agregar_actividad.html'
    success_url = reverse_lazy('listar_actividades')

class ActividadesUpdateView(UpdateView):

    model = Actividades 
    fields = ['nombre', 'descripcion', 'nivel_dificultad', 'equipo_requerimiento', 'recomendacion_salud', 'estado','apto_para_menores']
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

class TarifaCreateView(CreateView):
    model = Tarifa
   
    fields = ['paquete', 'temporada', 'precio_adulto', 'precio_menor']
    template_name = 'admin/tarifas/agregar_tarifa.html'
    success_url = reverse_lazy('listar_tarifas')

class TarifaUpdateView(UpdateView):
    model = Tarifa
    fields = ['paquete', 'temporada', 'precio_adulto', 'precio_menor']
    template_name = 'admin/tarifas/editar_tarifa.html'
    success_url = reverse_lazy('listar_tarifas')
#temporada
class TemporadaListView(ListView):
    model = Temporada
    template_name = 'admin/temporada/temporada.html'
    context_object_name = 'temporadas'
class TemporadaCreateView(CreateView):
    model = Temporada
    fields = ['nombre', 'fecha_inicio', 'fecha_fin']
    template_name = 'admin/temporada/agregar_temporada.html'
    success_url = reverse_lazy('listar_temporadas')
class TemporadaUpdateView(UpdateView):
    model = Temporada
    fields = ['nombre', 'fecha_inicio', 'fecha_fin']
    template_name = 'admin/temporada/editar_temporada.html'
    success_url = reverse_lazy('listar_temporadas')

    