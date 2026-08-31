from App.forms.temporada.forms import TemporadaForm
from django.views.generic import ListView
from django.db.models import Count, Q
from App.models import *
from App.utils import crear_notificacion_sistema
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from datetime import datetime
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy


# Create your views here.
class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin para asegurar que solo usuarios autenticados con permisos
    de staff/administrador puedan acceder a las vistas administrativas.
    """
    def test_func(self):
        return self.request.user.is_active and self.request.user.is_staff

class TemporadaListView(StaffRequiredMixin, ListView):
    model = Temporada
    template_name = 'temporada/temporada.html'
    context_object_name = 'temporadas'

    def get_queryset(self):
        queryset = Temporada.objects.all()
        fecha_inicio = self.request.GET.get("fecha_inicio", "").strip()
        fecha_fin = self.request.GET.get("fecha_fin", "").strip()

      
        if fecha_inicio:
            try:
                f_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_inicio__gte=f_inicio)
            except ValueError:
                pass

        if fecha_fin:
            try:
                f_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_fin__lte=f_fin)
            except ValueError:
                pass

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


class TemporadaCreateView(StaffRequiredMixin, CreateView):
    model = Temporada
    form_class = TemporadaForm
    template_name = 'temporada/agregar_temporada.html'
    success_url = reverse_lazy('listar_temporadas')

    def form_valid(self, form):
        # Validar que fecha_fin no sea anterior a fecha_inicio
        fecha_inicio = form.cleaned_data.get('fecha_inicio')
        fecha_fin = form.cleaned_data.get('fecha_fin')

        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            form.add_error('fecha_fin', "La fecha de finalización no puede ser anterior a la fecha de inicio.")
            return self.form_invalid(form)

        response = super().form_valid(form)
        crear_notificacion_sistema(
            usuario=self.request.user,
            accion="NUEVA TEMPORADA CREADA",
            tabla_afectada="Temporadas",
            observacion=f"Se ha registrado con éxito la temporada: '{self.object.nombre}'.",
            valor_anterior="Ninguno (Registro Nuevo)",
            nuevo_valor=f"Nombre: {self.object.nombre}, Inicio: {self.object.fecha_inicio}, Fin: {self.object.fecha_fin}"
        )
        return response


class TemporadaUpdateView(StaffRequiredMixin, UpdateView):
    model = Temporada
    form_class = TemporadaForm
    template_name = 'temporada/editar_temporada.html'
    success_url = reverse_lazy('listar_temporadas')

    def form_valid(self, form):
        fecha_inicio = form.cleaned_data.get('fecha_inicio')
        fecha_fin = form.cleaned_data.get('fecha_fin')

        if fecha_inicio and fecha_fin and fecha_fin < fecha_inicio:
            form.add_error('fecha_fin', "La fecha de finalización no puede ser anterior a la fecha de inicio.")
            return self.form_invalid(form)

        temp_antigua = self.get_object()
        valor_viejo = f"Nombre: {temp_antigua.nombre}, Inicio: {temp_antigua.fecha_inicio}, Fin: {temp_antigua.fecha_fin}, Estado: {temp_antigua.estado}"

        response = super().form_valid(form)

        valor_nuevo = f"Nombre: {self.object.nombre}, Inicio: {self.object.fecha_inicio}, Fin: {self.object.fecha_fin}, Estado: {self.object.estado}"

        crear_notificacion_sistema(
            usuario=self.request.user,
            accion="TEMPORADA MODIFICADA",
            tabla_afectada="Temporadas",
            observacion=f"La temporada '{self.object.nombre}' ha sido actualizada correctamente.",
            valor_anterior=valor_viejo,
            nuevo_valor=valor_nuevo
        )
        return response