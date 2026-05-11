from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import PQRS, Blog


#PQRS
class PQRSListView(ListView):
    model = PQRS
    template_name = 'admin/pqrs/pqrs.html' 
    context_object_name = 'pqrs'
class PQRSCreateView(CreateView):
    model = PQRS
    fields = ['cliente', 'tipo', 'asunto', 'descripcion', 'estado', 'respuesta']
    template_name = 'admin/pqrs/agregar_pqrs.html'
    success_url = reverse_lazy('comunidad:listar_pqrs')
class PQRSUpdateView(UpdateView):
    model = PQRS
    fields = ['cliente', 'tipo', 'asunto', 'descripcion', 'estado', 'respuesta']
    template_name = 'admin/pqrs/editar_pqrs.html'
    success_url = reverse_lazy('comunidad:listar_pqrs')
class PQRSDeleteView(DeleteView):
    model = PQRS
    template_name = 'admin/pqrs/eliminar_pqrs.html'
    success_url = reverse_lazy('comunidad:listar_pqrs')
    




#BLOG
class BlogListView(ListView):
    model = Blog
    template_name = 'public/blog/blog.html' 
    context_object_name = 'blogs'
class BlogCreateView(CreateView):
    model = Blog
    fields = ['titulo', 'contenido', 'resumen', 'imagen', 'categoria', 'publicado']
    template_name = 'admin/blog/agregar_blog.html'
    success_url = reverse_lazy('comunidad:listar_blog')
class BlogUpdateView(UpdateView):
    model = Blog
    fields = ['titulo', 'contenido', 'resumen', 'imagen', 'categoria', 'publicado']
    template_name = 'admin/blog/editar_blog.html'
    success_url = reverse_lazy('comunidad:listar_blog')
class BlogDeleteView(DeleteView):
    model = Blog
    template_name = 'admin/blog/eliminar_blog.html'
    success_url = reverse_lazy('comunidad:listar_blog')

@login_required
def resenas_view(request):
    """
    Vista para visualizar las reseñas del usuario.
    Sigue el patrón MVT y permite gestionar comentarios propios.
    """
    context = {
        'resenas': [], # Aquí se filtrarían las reseñas del usuario: Resena.objects.filter(usuario=request.user)
        'total_resenas': 0,
        'promedio': 0.0,
    }
    return render(request, 'private/comentarios.html', context)
