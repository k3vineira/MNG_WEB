from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from .models import PQRS, Blog
from django.shortcuts import get_object_or_404
from .forms import PqrsForm , BlogForm
from django.contrib import messages
from usuarios.models import Cliente

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
    context_object_name = 'todas_las_pqrs' 
    
    def get_queryset(self):
        
        return PQRS.objects.all().order_by('-fecha')

def contestar_pqrs(request, pqrs_id):
    pqr = get_object_or_404(PQRS, pk=pqrs_id)
    if request.method == 'POST':
        
        pqr.respuesta = request.POST.get('respuesta') 
        pqr.save()
        return redirect('comunidad:listar_pqrs')
def guardar_pqrs(request):
    if request.method == 'POST':
        form = PqrsForm(request.POST, request.FILES)
        
        if form.is_valid():
            nueva_pqrs = form.save(commit=False)
        
            if request.user.is_authenticated:
                try:
                    cliente_obj = Cliente.objects.get(usuario=request.user)
                    nueva_pqrs.cliente = cliente_obj
                except Cliente.DoesNotExist:
                    pass 
            
            nueva_pqrs.save() 
            messages.success(request, "Tu PQRS ha sido radicada exitosamente.")
            return redirect('comunidad:pqrs')
        else:
            print(f"Errores del formulario: {form.errors}")
            messages.error(request, "Hubo un error en los datos. Por favor verifica los campos.")

    return redirect('comunidad:pqrs')


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
