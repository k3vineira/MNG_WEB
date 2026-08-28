from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import render
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q
from django.core.paginator import Paginator
from App.models import *
from App.utils import crear_notificacion_sistema
from App.forms import BlogForm

 
 
def blog(request):
    blogs_list = Blog.objects.filter(estado=True).order_by('-fecha_publicacion')
    paginator = Paginator(blogs_list, 6)  # Mostrar 6 blogs por página
    page_number = request.GET.get('page')
    blogs = paginator.get_page(page_number)
    context = {'blogs': blogs}
    return render(request, 'blog.html', context)


def detalle_blog(request, id):
    post = get_object_or_404(Blog, id=id)
    context = {'post': post}
    return render(request, 'detalle_blog.html', context)

# BLOG


class BlogListView(ListView):
    model = Blog
    template_name = 'admin/blog/blog.html'
    context_object_name = 'blogs'
    ordering = ['-id']

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

     
        stats = Blog.objects.aggregate(
            total=Count('id'),
            publicados=Count('id', filter=Q(estado=True)),
            borradores=Count('id', filter=Q(estado=False))
        )

        context['stats_list'] = [
            ('Total Blogs', stats['total'], 'text-dark'),
            ('Publicados', stats['publicados'], 'text-success'),
            ('Borradores', stats['borradores'], 'text-danger'),
        ]
        return context


class BlogCreateView(CreateView):
    model = Blog
    form_class = BlogForm
    template_name = 'admin/blog/agregar_blog.html'
    success_url = reverse_lazy('listar_blog')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        crear_notificacion_sistema(
            usuario=self.request.user,
            titulo="Nueva Publicación Creada",
            mensaje=f"El artículo de blog '{self.object.titulo}' ha sido publicado con éxito.",
            tipo='sistema'
        )
        return response


class BlogUpdateView(UpdateView):
    model = Blog
    form_class = BlogForm
    template_name = 'admin/blog/editar_blog.html'
    success_url = reverse_lazy('listar_blog')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        crear_notificacion_sistema(
            usuario=self.request.user,
            titulo=" Publicación Actualizada",
            mensaje=f"El artículo '{self.object.titulo}' ha sido modificado correctamente.",
            tipo='sistema'
        )
        return response


class BlogDeleteView(DeleteView):
    model = Blog
    template_name = 'admin/blog/eliminar_blog.html'
    success_url = reverse_lazy('listar_blog')
    
    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        titulo_blog = self.object.titulo  # Guardamos el título antes de borrar el registro
        response = super().delete(request, *args, **kwargs)
        
        crear_notificacion_sistema(
            usuario=request.user,
            titulo=" Publicación Eliminada",
            mensaje=f"Se ha eliminado permanentemente el artículo: '{titulo_blog}'.",
            tipo='sistema'
        )
        return response


def blog_usuario(request):
    articulos = Blog.objects.filter(
        estado=True).order_by('-fecha_publicacion')
    context = {'blogs': articulos}
    return render(request, 'blog.html', context)
