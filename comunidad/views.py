from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import render, redirect
from .models import PQRS, Blog
from django.shortcuts import get_object_or_404
from .forms import PqrsForm, BlogForm
from django.contrib import messages
from core.decoradores import requiere_autenticacion, requiere_administrador
from usuarios.models import Cliente
from django.db.models import Count, Q
from notificaciones.models import Notificacion
from notificaciones.utils import crear_notificacion_sistema


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


@requiere_autenticacion
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
    
    def form_valid(self, form):
        response = super().form_valid(form)
        crear_notificacion_sistema(
            usuario=self.request.user,
            titulo="✍️ Nueva Publicación Creada",
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
            titulo="✏️ Publicación Actualizada",
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
            titulo="🗑️ Publicación Eliminada",
            mensaje=f"Se ha eliminado permanentemente el artículo: '{titulo_blog}'.",
            tipo='sistema'
        )
        return response


def blog_usuario(request):
    articulos = Blog.objects.filter(
        publicado=True).order_by('-fecha_publicacion')
    context = {'blogs': articulos}
    return render(request, 'usuario/blog.html', context)

# --- VIEWS EXTRAÍDAS DE USUARIOS ---

from .models import Comentario

@requiere_autenticacion
def enviar_comentario(request):
    """Renderiza el histórico de opiniones y procesa las nuevas reseñas de paquetes."""
    if request.method == 'POST':
        tipo = request.POST.get('tipo', 'experiencia')
        titulo = request.POST.get('titulo')
        mensaje = request.POST.get('mensaje')
        valoracion = request.POST.get('valoracion', 5)
        paquete_id = request.POST.get('paquete_id')

        Comentario.objects.create(
            usuario=request.user,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            valoracion=valoracion,
            paquete_id=paquete_id if paquete_id else None
        )
        messages.success(request, 'Comentario enviado exitosamente.')
        return redirect('mis_resenas')

    return render(request, 'comunidad/private_comentarios.html', {
        'titulo': 'Comunidad Monagua — Reseñas y Experiencias'
    })

@requiere_administrador
def listar_comentarios(request):
    """Renderiza el módulo de moderación y auditoría de comentarios para el Staff."""
    comentarios = Comentario.objects.all().select_related(
        'usuario', 'paquete').order_by('-fecha_creacion')
    return render(request, 'comunidad/admin_comentarios.html', {
        'titulo': 'Moderación de Comentarios — Administración',
        'comentarios': comentarios
    })

@requiere_administrador
def toggle_visible(request, pk):
    """Acción de backend para alternar la visibilidad pública de un comentario (Redirecciona)."""
    if request.method == 'POST':
        comentario = get_object_or_404(Comentario, pk=pk)
        comentario.visible = not comentario.visible
        comentario.save()
        estado = 'visible' if comentario.visible else 'oculto'
        messages.info(request, f'Comentario marcado como {estado}.')
    return redirect('listar_comentarios')


@requiere_administrador
def responder_comentario(request, pk):
    """Acción de backend para almacenar la respuesta oficial del administrador (Redirecciona)."""
    if request.method == 'POST':
        comentario = get_object_or_404(Comentario, pk=pk)
        comentario.admin_respuesta = request.POST.get('admin_respuesta', '')
        comentario.save()
        messages.success(request, 'Respuesta guardada correctamente.')
    return redirect('listar_comentarios')


@requiere_autenticacion
def mis_resenas_view(request):
    """
    Renderiza el panel de reseñas del turista.
    Procesa el envío de nuevas experiencias y distribuye las métricas globales.
    """
    if request.method == 'POST':
        tipo = request.POST.get('tipo', 'experiencia')
        titulo = request.POST.get('titulo')
        mensaje = request.POST.get('mensaje')
        valoracion = request.POST.get('valoracion', 5)
        paquete_id = request.POST.get('paquete_id')

        Comentario.objects.create(
            usuario=request.user,
            tipo=tipo,
            titulo=titulo,
            mensaje=mensaje,
            valoracion=valoracion,
            paquete_id=paquete_id if paquete_id else None
        )
        messages.success(request, 'Gracias por tu reseña.')
        return redirect('mis_resenas')

    comentarios = Comentario.objects.filter(
        usuario=request.user).order_by('-fecha_creacion')
    return render(request, 'comunidad/private_resenas.html', {
        'titulo': 'Mis Experiencias y Reseñas — Monagua',
        'comentarios': comentarios
    })
