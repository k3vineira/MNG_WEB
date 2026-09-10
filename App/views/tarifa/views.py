from django.views.generic import ListView
from django.db.models import Count, Q
from App.models import *
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from App.utils import crear_notificacion_sistema
from App.forms.tarifa.forms import TarifaForm
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView,UpdateView


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Mixin para asegurar que solo usuarios autenticados con permisos
    de staff/administrador puedan acceder a las vistas administrativas.
    """
    def test_func(self):
        return self.request.user.is_active and self.request.user.is_staff

class TarifaListView(StaffRequiredMixin, ListView):
    model = Tarifa
    template_name = 'admin/tarifa/tarifas.html'
    context_object_name = 'tarifas'

    def get_queryset(self):
        queryset = super().get_queryset().select_related('paquete', 'temporada')
        paquete_id = self.request.GET.get('paquete', '').strip()
        if paquete_id:
            try:
                p_id = int(paquete_id)
                if p_id > 0:
                    queryset = queryset.filter(paquete_id=p_id)
            except (ValueError, TypeError):
                pass
        return queryset.order_by('-id')

    def get_context_data(self, **kwargs):
     context = super().get_context_data(**kwargs)
    
    # Cálculo de métricas generales sobre todas las tarifas
     stats = Tarifa.objects.aggregate(
        total=Count('id'),
        activas=Count('id', filter=Q(estado=True)),
        inactivas=Count('id', filter=Q(estado=False))
    )
    
     context.update(stats)
    
    # Estructura limpia para renderizar las tarjetas en la plantilla HTML
     context['stats_list'] = [
        ('Total', stats['total'] or 0, 'text-dark'),
        ('Activas', stats['activas'] or 0, 'text-success'),
        ('Inactivas', stats['inactivas'] or 0, 'text-danger'),
    ]
    
    # Mantiene el estado de los filtros seleccionados en la interfaz
     context['paquetes'] = Paquete.objects.all()
     context['paquete_seleccionado'] = self.request.GET.get('paquete', '')
     context['estado_seleccionado'] = self.request.GET.get('estado', '')
    
     return context


class TarifaCreateView(StaffRequiredMixin, CreateView):
    model = Tarifa
    form_class = TarifaForm
    template_name = 'admin/tarifa/agregar_tarifa.html'
    success_url = reverse_lazy('listar_tarifas')

    def form_valid(self, form):
        # Validar lógica de negocio: Precios no negativos
        precio_adulto = form.cleaned_data.get('precio_adulto')
        precio_menor = form.cleaned_data.get('precio_menor')

        if (precio_adulto is not None and precio_adulto < 0) or (precio_menor is not None and precio_menor < 0):
            form.add_error(None, "Los precios no pueden ser valores negativos.")
            return self.form_invalid(form)

        response = super().form_valid(form)
        crear_notificacion_sistema(
            usuario=self.request.user,
            accion="NUEVA TARIFA CREADA",
            tabla_afectada="Tarifas",
            observacion=f"Se ha registrado una tarifa para el paquete: {self.object.paquete}.",
            valor_anterior="Ninguno (Registro Nuevo)",
            nuevo_valor=f"Adulto: ${self.object.precio_adulto}, Menor: ${self.object.precio_menor}"
        )
        return response

 
class TarifaUpdateView(StaffRequiredMixin, UpdateView):
    model = Tarifa
    form_class = TarifaForm
    template_name = 'admin/tarifa/editar_tarifa.html'
    success_url = reverse_lazy('listar_tarifas')

    def form_valid(self, form):
        precio_adulto = form.cleaned_data.get('precio_adulto')
        precio_menor = form.cleaned_data.get('precio_menor')

        if (precio_adulto is not None and precio_adulto < 0) or (precio_menor is not None and precio_menor < 0):
            form.add_error(None, "Los precios no pueden ser valores negativos.")
            return self.form_invalid(form)

        tarifa_antigua = self.get_object()
        valor_viejo = f"Adulto: ${tarifa_antigua.precio_adulto}, Menor: ${tarifa_antigua.precio_menor}, Estado: {tarifa_antigua.estado}"

        response = super().form_valid(form)

        valor_nuevo = f"Adulto: ${self.object.precio_adulto}, Menor: ${self.object.precio_menor}, Estado: {self.object.estado}"

        crear_notificacion_sistema(
            usuario=self.request.user,
            accion="TARIFA MODIFICADA",
            tabla_afectada="Tarifas",
            observacion=f"Los datos de la tarifa de '{self.object.paquete}' han sido actualizados.",
            valor_anterior=valor_viejo,
            nuevo_valor=valor_nuevo
        )
        return response
