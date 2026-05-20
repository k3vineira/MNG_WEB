from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import render
from .models import Reserva, Cancelacion
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from catalogo.models import Paquete


# =========================
# RESERVAS ADMIN
# =========================

class ReservaListView(ListView):
    model = Reserva
    template_name = 'admin/reservas/reservas.html'
    context_object_name = 'reservas'


class ReservaCreateView(CreateView):
    model = Reserva
    fields = [
        'cliente',
        'paquete',
        'horario',
        'num_personas',
        'estado',
        'observaciones'
    ]

    template_name = 'admin/reservas/agregar_reserva.html'
    success_url = reverse_lazy('listar_reservas')


class ReservaUpdateView(UpdateView):
    model = Reserva

    fields = [
        'cliente',
        'paquete',
        'horario',
        'num_personas',
        'estado',
        'observaciones'
    ]

    template_name = 'admin/reservas/editar_reserva.html'
    success_url = reverse_lazy('listar_reservas')


class ReservaDeleteView(DeleteView):
    model = Reserva
    template_name = 'admin/reservas/eliminar_reserva.html'
    success_url = reverse_lazy('listar_reservas')


# =========================
# CANCELACIONES
# =========================

class CancelacionListView(ListView):
    model = Cancelacion
    template_name = 'admin/cancelaciones/cancelaciones.html'
    context_object_name = 'cancelaciones'


class CancelacionCreateView(CreateView):
    model = Cancelacion
    fields = ['reserva', 'motivo', 'penalidad']

    template_name = 'admin/cancelaciones/agregar_cancelacion.html'
    success_url = reverse_lazy('listar_cancelaciones')


class CancelacionUpdateView(UpdateView):
    model = Cancelacion
    fields = ['reserva', 'motivo', 'penalidad']

    template_name = 'admin/cancelaciones/editar_cancelacion.html'
    success_url = reverse_lazy('listar_cancelaciones')


class CancelacionDeleteView(DeleteView):
    model = Cancelacion
    template_name = 'admin/cancelaciones/eliminar_cancelacion.html'
    success_url = reverse_lazy('listar_cancelaciones')


# =========================
# VISTA PÚBLICA
# =========================

def reservas_view(request):
    """
    Vista pública.
    El template decide si mostrar el formulario
    o pedir inicio de sesión.
    """

    paquetes = Paquete.objects.all()
    
    paquete_id = request.GET.get('paquete_id')
    paquete = None
    if paquete_id:
        paquete = get_object_or_404(Paquete, id=paquete_id)

    context = {
        'paquetes': paquetes,
        'paquete': paquete
    }

    return render(
        request,
        'usuario/reservas.html',
        context
    )


# =========================
# VISTA PÚBLICA
# =========================

@login_required 
def guardar_reserva(request, paquete_id):
    if request.method == 'POST':
        paquete = get_object_or_404(Paquete, id=paquete_id)
        fecha_viaje = request.POST.get('fecha')
        
        # Extraer los pasajeros según los nuevos nombres de input
        adultos = int(request.POST.get('adultos', 1))
        menores = int(request.POST.get('menores', 0))
        
        if fecha_viaje:
            # Crear la reserva usando la estructura normalizada
            reserva= Reserva.objects.create(
                usuario=request.user,       
                paquete=paquete,            
                fecha=fecha_viaje,
                numero_adultos=adultos,
                numero_menores=menores
            )
            # El save() del modelo Reserva automáticamente calcula y asigna el monto_total
            
            messages.success(request, f"¡Reserva para {paquete.nombre} realizada con éxito!")
            return redirect(f"/reservas/reservar/?paquete_id={paquete_id}")
        else:
            messages.error(request, "Por favor completa todos los campos.")

    return redirect('reservas')
