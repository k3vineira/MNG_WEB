from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from .models import PQRS, Blog
from django.shortcuts import get_object_or_404
from .forms import PqrsForm, BlogForm
from django.contrib import messages
from usuarios.models import Cliente
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from notificaciones.models import Notificacion


def blog(request):
    blogs = Blog.objects.filter(publicado=True).order_by('-fecha_publicacion')
    context = {'blogs': blogs}
    return render(request, 'usuario/blog.html', context)


def detalle_blog(request, id):
    post = get_object_or_404(Blog, id=id)
    context = {'post': post}
    return render(request, 'usuario/detalle_blog.html', context)


def pqrs(request):
    pqrs = PQRS.objects.all()
    form = PqrsForm()
    context = {'pqrs': pqrs, 'form': form}
    return render(request, 'usuario/pqrs.html', context)


# PQRS
class PQRSListView(ListView):
    model = PQRS
    template_name = 'admin/pqrs/pqrs.html'
    context_object_name = 'todas_las_pqrs'

    def get_queryset(self):

        return PQRS.objects.all().order_by('-fecha')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        stats = PQRS.objects.aggregate(
            total=Count('id'),
            respondidas=Count('id', filter=Q(
                respuesta__isnull=False) & ~Q(respuesta='')),
            pendientes=Count('id', filter=Q(
                respuesta__isnull=True) | Q(respuesta=''))
        )

        context['stats_list'] = [
            ('Total PQRS', stats['total'], 'text-dark'),
            ('Respondidas', stats['respondidas'], 'text-success'),
            ('Pendientes', stats['pendientes'], 'text-danger'),
        ]

        return context


def contestar_pqrs(request, pqrs_id):
    pqr = get_object_or_404(PQRS, pk=pqrs_id)
    if request.method == 'POST':
        pqr.respuesta = request.POST.get('respuesta')
        pqr.estado = 'cerrado'
        pqr.save()  

        if pqr.cliente and pqr.cliente.usuario:
            Notificacion.objects.create(
                cliente=pqr.cliente.usuario,
                titulo="PQRS Respondida",
                mensaje=f"El administrador ha respondido a tu solicitud sobre: '{pqr.asunto or 'Tu PQRS'}'.",
                tipo='pqrs'  
            )
        return redirect('listar_pqrs')


def guardar_pqrs(request):
    if request.method == 'POST':
        form = PqrsForm(request.POST)
        if form.is_valid():
            nueva_pqrs = form.save(commit=False)
            if request.user.is_authenticated:
                try:
                    cliente_obj = Cliente.objects.get(usuario=request.user)
                    nueva_pqrs.cliente = cliente_obj
                except Cliente.DoesNotExist:
                    nueva_pqrs.cliente = None
            nueva_pqrs.estado = 'abierto'

            nueva_pqrs.save()
            messages.success(request, "Tu PQRS ha sido radicada con éxito.")
            return redirect('mis_pqrs')
        else:
            print(f"--- ERRORES DEL FORMULARIO: {form.errors} ---")
            messages.error(
                request, "Por favor verifica los campos del formulario.")

    return redirect('mis_pqrs')


@login_required
def mis_pqrs_view(request):
    from usuarios.models import Cliente
    solicitudes_usuario = PQRS.objects.none()
    try:
        cliente_obj = Cliente.objects.get(usuario=request.user)
        solicitudes_usuario = PQRS.objects.filter(cliente=cliente_obj)
    except Cliente.DoesNotExist:
        pass

    form = PqrsForm()
    context = {
        'solicitudes': solicitudes_usuario,
        'form': form,
    }
    return render(request, 'usuario/mis_pqrs.html', context)

# BLOG


class BlogListView(ListView):
    model = Blog
    template_name = 'admin/blog/blog.html'
    context_object_name = 'blogs'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Conteo de publicados vs borradores
        stats = Blog.objects.aggregate(
            total=Count('id'),
            publicados=Count('id', filter=Q(publicado=True)),
            borradores=Count('id', filter=Q(publicado=False))
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


class BlogUpdateView(UpdateView):
    model = Blog
    form_class = BlogForm
    template_name = 'admin/blog/editar_blog.html'
    success_url = reverse_lazy('listar_blog')


class BlogDeleteView(DeleteView):
    model = Blog
    template_name = 'admin/blog/eliminar_blog.html'
    success_url = reverse_lazy('listar_blog')


def blog_usuario(request):
    articulos = Blog.objects.filter(
        publicado=True).order_by('-fecha_publicacion')
    context = {'blogs': articulos}
    return render(request, 'usuario/blog.html', context)
