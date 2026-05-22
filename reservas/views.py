from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import render
from .models import Reserva, Cancelacion
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from catalogo.models import Paquete
from .forms import ReservaForm , CancelacionForm
from decimal import Decimal, InvalidOperation
from .forms import CancelacionForm



# =========================
# RESERVAS ADMIN
# =========================

class ReservaListView(ListView):
    model = Reserva
    template_name = 'admin/reservas/reservas.html'
    context_object_name = 'reservas'

    def get_queryset(self):
        return Reserva.objects.exclude(estado='cancelada').order_by('-id')


class ReservaCreateView(CreateView):
    model = Reserva
    form_class = ReservaForm
   # fields = ['usuario','paquete','fecha','numero_adultos','numero_menores','estado', ]
    template_name = 'admin/reservas/agregar_reserva.html'
    success_url = reverse_lazy('listar_reservas')


class ReservaUpdateView(UpdateView):
    model = Reserva
    form_class = ReservaForm
    # fields = ['usuario','paquete','fecha','numero_adultos','numero_menores','estado', ]
    template_name = 'admin/reservas/editar_reserva.html'
    success_url = reverse_lazy('listar_reservas')


class ReservaDeleteView(DeleteView):
    model = Reserva
    template_name = 'admin/reservas/eliminar_reserva.html'
    success_url = reverse_lazy('listar_reservas')

@login_required(login_url='login')
def mis_reservas_usuario(request):
    reservas_canceladas_ids = Cancelacion.objects.filter(reserva__usuario=request.user).values_list('reserva_id', flat=True)
    mis_reservas = Reserva.objects.filter(usuario=request.user).exclude(id__in=reservas_canceladas_ids).order_by('-id')
    
    context = {
        'reservas': mis_reservas
    }
    return render(request, 'usuario/mis_reservas.html', context)



# =========================
# CANCELACIONES
# =========================

class CancelacionListView(ListView):
    model = Cancelacion
    template_name = 'admin/cancelaciones/cancelaciones_admin.html'
    context_object_name = 'cancelaciones'


class CancelacionCreateView(CreateView):
    model = Cancelacion
    fields = ['motivo']
    template_name = 'usuario/cancelaciones/crear_cancelacion.html' 
    success_url = reverse_lazy('mis_cancelaciones_usuario') 
    def form_valid(self, form):
        reserva_id = self.request.GET.get('reserva_id')
        if reserva_id:
            reserva = get_object_or_404(Reserva, id=reserva_id)
            form.instance.reserva = reserva
            
        form.instance.usuario = self.request.user
        return super().form_valid(form)

class CancelacionUpdateView(UpdateView):
    model = Cancelacion
    form_class = CancelacionForm
    template_name = 'admin/cancelaciones/editar_cancelacion.html'
    success_url = reverse_lazy('administrar_cancelaciones')


class CancelacionDeleteView(DeleteView):
    model = Cancelacion
    template_name = 'admin/cancelaciones/eliminar_cancelacion.html'
    success_url = reverse_lazy('administrar_cancelaciones')
    

@login_required(login_url='login')
def mis_cancelaciones_usuario(request):
   
    mis_cancelaciones = Cancelacion.objects.filter(reserva__usuario=request.user).order_by('-id')
    
    context = {
        'cancelaciones': mis_cancelaciones
    }
    return render(request, 'usuario/cancelaciones/mis_cancelaciones.html', context)

def administrar_cancelaciones(request):
    if request.method == 'POST':
        cancelacion_id = request.POST.get('cancelacion_id')
        cancelacion = get_object_or_404(Cancelacion, id=cancelacion_id)
        
        cancelacion.estado = request.POST.get('estado')
        
        penalidad_raw = request.POST.get('penalidad', '0').strip()
        try:
            cancelacion.penalidad = Decimal(penalidad_raw) if penalidad_raw else Decimal('0.00')
        except (InvalidOperation, ValueError):
            cancelacion.penalidad = Decimal('0.00')
            
        cancelacion.save()
    
        if cancelacion.estado == 'aceptada':
            cancelacion.reserva.estado = 'cancelada'
        elif cancelacion.estado == 'rechazada':
            cancelacion.reserva.estado = 'activa'
        else:
            cancelacion.reserva.estado = 'pendiente'
            
        cancelacion.reserva.save()
            
        return redirect('administrar_cancelaciones')

    cancelaciones_raw = Cancelacion.objects.all().order_by('-id')

    for c in cancelaciones_raw:
        try:
            Decimal(str(c.penalidad))
        except (InvalidOperation, ValueError, TypeError):
            c.penalidad = Decimal('0.00')

    return render(request, 'admin/cancelaciones/cancelaciones_admin.html', {'cancelaciones': cancelaciones_raw})

 

# VISTA PÚBLICA
# =========================

def reservas_view(request):
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
            
            messages.success(request, f"¡Reserva para {paquete.nombre} realizada con éxito!")
            return redirect(f"/reservas/reservar/?paquete_id={paquete_id}")
        else:
            messages.error(request, "Por favor completa todos los campos.")

    return redirect('reservas')
