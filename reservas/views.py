from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.shortcuts import render
from .models import Reserva, Cancelacion
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from catalogo.models import Paquete
from .forms import ReservaForm , CancelacionForm
from decimal import Decimal, InvalidOperation
from .forms import CancelacionForm
from django.core.mail import send_mail
from datetime import datetime
from catalogo.models import Tarifa
from django.conf import settings
from django.contrib import messages
from django.db.models import Count, Q
from core.utils import plantilla_reserva_html, plantilla_cancelacion_html, enviar_correo_html_monagua


# =========================
# RESERVAS ADMIN
# =========================

class ReservaListView(ListView):
    model = Reserva
    template_name = 'admin/reservas/reservas.html'
    context_object_name = 'reservas'

    def get_queryset(self):
        return Reserva.objects.exclude(estado='cancelada').order_by('-id')
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        stats = Reserva.objects.aggregate(
            total=Count('id'),
            pendientes=Count('id', filter=Q(estado='pendiente')),
            confirmadas=Count('id', filter=Q(estado='confirmada')),
            canceladas=Count('id', filter=Q(estado='cancelada'))
        )
        context.update(stats)

        context['stats_list'] = [
            ('Total', stats['total'], 'text-dark'),
            ('Pendientes', stats['pendientes'], 'text-warning'),
            ('Confirmadas', stats['confirmadas'], 'text-success'),
            ('Canceladas', stats['canceladas'], 'text-danger'),
        ]
        return context


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

def enviar_correo_monagua(asunto, mensaje, destinatario):
    send_mail(
        asunto,
        mensaje,
        settings.EMAIL_HOST_USER,
        [destinatario],
        fail_silently=False,
    )

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
            cancelacion.reserva.estado = 'confirmada'
        else:
            cancelacion.reserva.estado = 'pendiente'
            
        cancelacion.reserva.save()
        
        asunto = f"Actualización de cancelación - Monagua"
        nombre_cliente = cancelacion.reserva.usuario.first_name or cancelacion.reserva.usuario.username
       
        if cancelacion.estado == 'aceptada':
            mensaje_texto = f"Hola {nombre_cliente}, tu solicitud de cancelación para {cancelacion.reserva.paquete.nombre} ha sido aceptada."
        elif cancelacion.estado == 'rechazada':
            mensaje_texto = f"Hola {nombre_cliente}, tu solicitud de cancelación para {cancelacion.reserva.paquete.nombre} ha sido rechazada."
        else:
            mensaje_texto = f"Hola {nombre_cliente}, tu solicitud de cancelación para {cancelacion.reserva.paquete.nombre} está en revisión."
            
        
        html_cancelacion = plantilla_cancelacion_html(
            nombre_cliente=nombre_cliente,
            paquete=cancelacion.reserva.paquete.nombre,
            estado=cancelacion.estado,
            penalidad=cancelacion.penalidad
        )
        
        
        enviar_correo_html_monagua(asunto, mensaje_texto, cancelacion.reserva.usuario.email, html_cancelacion)
            
        return redirect('administrar_cancelaciones')
    stats = Cancelacion.objects.aggregate(
        total=Count('id'),
        revisando=Count('id', filter=Q(estado__in=['pendiente', 'revision'])),
        aceptadas=Count('id', filter=Q(estado__in=['confirmada', 'aceptada'])),
        rechazadas=Count('id', filter=Q(estado__in=['cancelada', 'rechazada']))
    )
    
    stats_list = [
          ('Total', stats['total'], 'text-dark'),
           ('En Revisión', stats['revisando'], 'text-warning'),
           ('Aceptadas', stats['aceptadas'], 'text-success'),
          ('Rechazadas', stats['rechazadas'], 'text-danger'),
     ]

    cancelaciones_raw = Cancelacion.objects.all().order_by('-id')

    for c in cancelaciones_raw:
        try:
            Decimal(str(c.penalidad))
        except (InvalidOperation, ValueError, TypeError):
            c.penalidad = Decimal('0.00')

    return render(request, 'admin/cancelaciones/cancelaciones_admin.html', {'cancelaciones': cancelaciones_raw , 'stats_list': stats_list })

 

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
        
        # 1. Validación de fecha
        if not fecha_viaje:
            messages.error(request, "Por favor selecciona una fecha válida.")
            return redirect(f"/reservas/reservar/?paquete_id={paquete_id}")
            
        # 2. Convertir fecha y buscar tarifa en la base de datos
        fecha_date = datetime.strptime(fecha_viaje, '%Y-%m-%d').date()
        tarifa = Tarifa.objects.filter(
            paquete=paquete,
            temporada__fecha_inicio__lte=fecha_date,
            temporada__fecha_fin__gte=fecha_date
        ).first()
        
        # 3. Si no hay tarifa, no permitimos guardar
        if not tarifa:
            messages.error(request, "No hay tarifas disponibles para esta fecha. Por favor elige otra.")
            return redirect(f"/reservas/reservar/?paquete_id={paquete_id}")
            
        # 4. Obtener pasajeros
        try:
            adultos = int(request.POST.get('adultos', 1))
            menores = int(request.POST.get('menores', 0))
        except ValueError:
            adultos, menores = 1, 0
        
        # 5. Crear la reserva
        reserva = Reserva.objects.create(
            usuario=request.user,        
            paquete=paquete,            
            fecha=fecha_viaje,
            numero_adultos=adultos,
            numero_menores=menores,
            estado='pendiente' # O el estado inicial que manejes
        )
        
        asunto = "Confirmación de tu reserva en Monagua"
        nombre_cliente = request.user.first_name or request.user.username
        
        mensaje_texto = f"Hola {nombre_cliente}, hemos recibido tu solicitud de reserva para {paquete.nombre}."
        
        # Generamos el HTML usando tu plantilla bonita
        html_bonito = plantilla_reserva_html(
            nombre_cliente=nombre_cliente,
            paquete=paquete.nombre,
            fecha=fecha_viaje,
            adultos=adultos,
            menores=menores
        )
        
     
        enviar_correo_html_monagua(asunto, mensaje_texto, request.user.email, html_bonito)
        return redirect('mis_reservas_usuario') # Redirige a donde el usuario vea sus reservas

    return redirect('reservas')
