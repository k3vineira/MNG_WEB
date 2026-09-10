from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import render, get_object_or_404
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Count, Q
from django.core.paginator import Paginator
from App.models import Blog
from App.utils import crear_notificacion_sistema
from App.forms.blog.forms import BlogForm


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin para asegurar que solo usuarios autenticados con permisos
    de administrador/staff puedan acceder a las vistas del blog administrativo.
    """
    def test_func(self):
        return self.request.user.is_active and (
            self.request.user.is_staff or getattr(self.request.user, 'rol', None) == 'admin' or getattr(self.request.user, 'rol', None) == 1
        )


# ==============================================================================
# VISTAS PÚBLICAS DEL BLOG (TURISTA / CLIENTE)
# ==============================================================================

def blog(request):
    """Listado público de blogs con paginación."""
    blogs_list = Blog.objects.filter(estado=True).select_related('usuario').order_by('-fecha_publicacion')
    paginator = Paginator(blogs_list, 6)
    page_number = request.GET.get('page')
    blogs = paginator.get_page(page_number)
    context = {'blogs': blogs}
    return render(request, 'blog.html', context)


def detalle_blog(request, id):
    """Vista pública de detalle de un artículo de blog."""
    post = get_object_or_404(Blog.objects.select_related('usuario'), id=id)
    context = {'post': post}
    return render(request, 'detalle_blog.html', context)


# ==============================================================================
# VISTAS ADMINISTRATIVAS DEL BLOG (STAFF / ADMIN)
# ==============================================================================

class BlogListView(StaffRequiredMixin, ListView):
    """Listado administrativo y métricas de publicaciones de blog."""
    model = Blog
    template_name = 'admin/blog/blog.html'
    context_object_name = 'blogs'
    ordering = ['-fecha_publicacion', '-id']

    def get_queryset(self):
        return Blog.objects.select_related('usuario').order_by('-fecha_publicacion', '-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stats = Blog.objects.aggregate(
            total=Count('id'),
            publicados=Count('id', filter=Q(estado=True)),
            borradores=Count('id', filter=Q(estado=False))
        )
        context.update(stats)
        context['stats_list'] = [
            ('Total Publicaciones', stats['total'], 'text-dark'),
            ('Publicados', stats['publicados'], 'text-success'),
            ('Borradores', stats['borradores'], 'text-danger'),
        ]
        return context


class BlogCreateView(StaffRequiredMixin, CreateView):
    """Creación de una nueva entrada de blog."""
    model = Blog
    form_class = BlogForm
    template_name = 'admin/blog/agregar_blog.html'
    success_url = reverse_lazy('listar_blog')

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        response = super().form_valid(form)
        crear_notificacion_sistema(
            usuario=self.request.user,
            accion="NUEVA PUBLICACIÓN BLOG",
            tabla_afectada="Blog",
            observacion=f"Se publicó el artículo: '{self.object.titulo}'.",
            valor_anterior="Ninguno (Nuevo Registro)",
            nuevo_valor=f"Título: {self.object.titulo}, Estado: {'Publicado' if self.object.estado else 'Borrador'}"
        )
        messages.success(self.request, f"El artículo '{self.object.titulo}' ha sido creado exitosamente.")
        return response


class BlogUpdateView(StaffRequiredMixin, UpdateView):
    """Edición y actualización de una entrada de blog existente."""
    model = Blog
    form_class = BlogForm
    template_name = 'admin/blog/editar_blog.html'
    success_url = reverse_lazy('listar_blog')

    def form_valid(self, form):
        blog_antiguo = self.get_object()
        valor_viejo = f"Título: {blog_antiguo.titulo}, Estado: {blog_antiguo.estado}"
        response = super().form_valid(form)
        valor_nuevo = f"Título: {self.object.titulo}, Estado: {self.object.estado}"

        crear_notificacion_sistema(
            usuario=self.request.user,
            accion="PUBLICACIÓN BLOG MODIFICADA",
            tabla_afectada="Blog",
            observacion=f"Se actualizó el artículo: '{self.object.titulo}'.",
            valor_anterior=valor_viejo,
            nuevo_valor=valor_nuevo
        )
        messages.success(self.request, f"El artículo '{self.object.titulo}' ha sido actualizado correctamente.")
        return response


class BlogDeleteView(StaffRequiredMixin, DeleteView):
    """Eliminación permanente de una entrada de blog."""
    model = Blog
    template_name = 'admin/blog/eliminar_blog.html'
    context_object_name = 'blog'
    success_url = reverse_lazy('listar_blog')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        titulo_blog = self.object.titulo
        valor_viejo = f"ID: {self.object.id}, Título: {self.object.titulo}"

        response = super().delete(request, *args, **kwargs)

        crear_notificacion_sistema(
            usuario=request.user,
            accion="PUBLICACIÓN BLOG ELIMINADA",
            tabla_afectada="Blog",
            observacion=f"Se eliminó el artículo de blog: '{titulo_blog}'.",
            valor_anterior=valor_viejo,
            nuevo_valor="Registro Eliminado"
        )
        messages.success(request, f"El artículo '{titulo_blog}' ha sido eliminado exitosamente.")
        return response
