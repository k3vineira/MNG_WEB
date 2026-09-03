from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from App.models import PQRS, Seguimiento
from App.forms.pqrs.forms import PqrsForm
from django.views.generic import ListView
from django.db.models import Count, Q
from App.models import *
from core.decoradores import requiere_autenticacion
from App.utils import registrar_bitacora


def pqrs(request):
    mis_reservas = Reserva.objects.filter(usuario=request.user)
    form = PqrsForm(user=request.user)
    pqrs_usuario = PQRS.objects.filter(usuario=request.user)
    
    context = {
        'pqrs': pqrs_usuario,
        'form': form,
        'tiene_reservas': mis_reservas.exists()
    }
    return render(request, 'admin/pqrs/pqrs_usuario.html', context)



class PQRSListView(ListView):
    model = PQRS
    template_name = 'admin/pqrs/pqrs.html'
    context_object_name = 'todas_las_pqrs'

    def get_queryset(self):
        # Mantenemos tu ordenamiento agregando prefetch para optimizar la consulta de Seguimiento y Reserva
        return PQRS.objects.all().prefetch_related('seguimientos__reserva').order_by('-fecha')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        stats = PQRS.objects.aggregate(
            total=Count('id'),
            respondidas=Count('id', filter=Q(seguimientos__isnull=False)),
            pendientes=Count('id', filter=Q(seguimientos__isnull=True))
        )

        context['stats_list'] = [
            ('Total PQRS', stats['total'], 'text-dark'),
            ('Respondidas', stats['respondidas'], 'text-success'),
            ('Pendientes', stats['pendientes'], 'text-danger'),
        ]

        return context


def contestar_pqrs(request, pqrs_id):
    pqr = get_object_or_404(PQRS, id=pqrs_id)

    if pqr.estado == 'cerrado':
        messages.warning(request, "Esta solicitud ya ha sido respondida y se encuentra cerrada.")
        return redirect('listar_pqrs')

    if request.method == 'POST':
        respuesta_texto = request.POST.get('respuesta')
        
        # 1. Obtenemos el ID de la reserva enviado desde el formulario HTML
        reserva_id = request.POST.get('reserva')
        reserva_obj = None
        
        if reserva_id:
            reserva_obj = Reserva.objects.filter(id=reserva_id).first()

        if respuesta_texto:
            # 2. Creamos el Seguimiento asignando directamente la llave foránea 'reserva'
            seguimiento_creado = Seguimiento.objects.create(
                pqrs=pqr,
                usuario=request.user,
                reserva=reserva_obj,  # <--- Asignación agregada a Seguimiento
                respuesta=respuesta_texto
            )
            
            pqr.estado = 'cerrado'
            pqr.save()

            # Se conserva íntegra la bitácora que tenías
            registrar_bitacora(
                usuario=request.user,
                accion='RESPUESTA',
                modulo='Seguimiento',
                registro_id=seguimiento_creado.id,
                seguimiento=seguimiento_creado,
                pqrs=pqr,
                descripcion=f"Respuesta registrada para la PQRS #{pqr.id} ('{pqr.asunto}').",
                ip_origen=request.META.get('REMOTE_ADDR')
            )
            
            messages.success(request, "Respuesta enviada y solicitud cerrada con éxito.")
            return redirect('listar_pqrs')

    # Pasamos las reservas del cliente al template para poder seleccionarlas en el select HTML
    reservas_cliente = Reserva.objects.filter(usuario=pqr.usuario) if pqr.usuario else Reserva.objects.none()

    return render(request, 'admin/contestar_pqrs.html', {
        'pqr': pqr,
        'reservas_cliente': reservas_cliente
    })
def guardar_pqrs(request):
    if request.method == 'POST':
        # 1. Pasamos user=request.user para que el form filtre y valide las reservas del usuario
        form = PqrsForm(request.POST, user=request.user)

        if form.is_valid():
            # 2. Guardar la PQRS principal (sin la reserva)
            nueva_pqrs = form.save(commit=False)
            
            if request.user.is_authenticated:
                nueva_pqrs.usuario = request.user
            else:
                nueva_pqrs.usuario = None

            nueva_pqrs.estado = 'abierto'
            nueva_pqrs.save()

            # 3. Extraer la reserva elegida en el campo del formulario
            reserva_seleccionada = form.cleaned_data.get('reserva')

            # 4. Guardar OBLIGATORIAMENTE en la tabla Seguimiento la relación con la Reserva
            Seguimiento.objects.create(
                pqrs=nueva_pqrs,
                usuario=request.user if request.user.is_authenticated else None,
                reserva=reserva_seleccionada,
                respuesta=f"Solicitud radicada inicialmente sobre la Reserva #{reserva_seleccionada.id}"
            )

            messages.success(request, f"Tu PQRS ha sido radicada con éxito para la Reserva #{reserva_seleccionada.id}.")
            return redirect('mis_pqrs')
        else:
            print(f"--- ERRORES DEL FORMULARIO: {form.errors} ---")
            messages.error(request, "Por favor verifica los campos del formulario.")

    return redirect('mis_pqrs')

@requiere_autenticacion
def mis_pqrs_view(request):

    solicitudes_usuario = PQRS.objects.filter(usuario=request.user).prefetch_related('seguimientos').order_by('-fecha')

    if request.method == 'POST':
        form = PqrsForm(request.POST)
        if form.is_valid():
            nueva_pqrs = form.save(commit=False)
            nueva_pqrs.usuario = request.user  # Asignación directa al usuario actual
            nueva_pqrs.save()
            
            messages.success(request, "Tu solicitud ha sido enviada correctamente.")
            return redirect('admin/pqrs/mis_pqrs')
    else:
        form = PqrsForm()

    context = {
        'solicitudes': solicitudes_usuario,
        'form': form,
    }
    return render(request, 'admin/pqrs/mis_pqrs.html', context)