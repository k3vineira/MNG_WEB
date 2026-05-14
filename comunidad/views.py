from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from .models import PQRS, Blog
from .forms import PqrsForm , BlogForm

def blog(request):
    blogs = Blog.objects.all()
    return render(request, 'usuario/blog.html', {'blogs': blogs})

def pqrs(request):
    pqrs = PQRS.objects.all()
    form = PqrsForm()
    
    return render(request, 'usuario/pqrs.html', {'pqrs': pqrs, 'form': form})

def guardar_pqrs(request):
    if request.method == 'POST':
        form = PqrsForm(request.POST)
        if form.is_valid():
            form.save() 
            return redirect('comunidad:pqrs') 
    else:
        form = PqrsForm()
    
    return render(request, 'usuario/pqrs.html', {'form': form})

#PQRS
class PQRSListView(ListView):
    model = PQRS
    template_name = 'admin/pqrs/pqrs.html' 
    context_object_name = 'pqrs'
class PQRSCreateView(CreateView):
    model = PQRS
    form = PqrsForm()
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
    template_name = 'admin/blog/blog.html' 
    context_object_name = 'blogs'
class BlogCreateView(CreateView):
    model = Blog
    form = BlogForm()
    fields = ['titulo', 'contenido', 'imagen', 'publicado']
    template_name = 'admin/blog/agregar_blog.html'
    success_url = reverse_lazy('comunidad:listar_blog')
class BlogUpdateView(UpdateView):
    model = Blog
    fields = ['titulo', 'contenido', 'imagen','publicado']
    template_name = 'admin/blog/editar_blog.html'
    success_url = reverse_lazy('comunidad:listar_blog')
class BlogDeleteView(DeleteView):
    model = Blog
    template_name = 'admin/blog/eliminar_blog.html'
    success_url = reverse_lazy('comunidad:listar_blog')
