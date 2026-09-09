from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView
from django.db.models import Count, Q

from App.models import PQRS, Seguimiento, Reserva
from App.forms.pqrs.forms import PqrsForm
from App.utils import registrar_bitacora


@login_required
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


@login_required
def contestar_pqrs(request, pqrs_id):
    pqr = get_object_or_404(PQRS, id=pqrs_id)

    if pqr.estado == 'cerrado':
        messages.warning(request, "Esta solicitud ya ha sido respondida y se encuentra cerrada.")
        return redirect('listar_pqrs')

    if request.method == 'POST':
        respuesta_texto = request.POST.get('respuesta')
        reserva_id = request.POST.get('reserva')
        reserva_obj = Reserva.objects.filter(id=reserva_id).first() if reserva_id else None

        if respuesta_texto:
            seguimiento_creado = Seguimiento.objects.create(
                pqrs=pqr,
                usuario=request.user,
                reserva=reserva_obj,
                respuesta=respuesta_texto
            )
            
            pqr.estado = 'cerrado'
            pqr.save()

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

    reservas_cliente = Reserva.objects.filter(usuario=pqr.usuario) if pqr.usuario else Reserva.objects.none()

    return render(request, 'admin/contestar_pqrs.html', {
        'pqr': pqr,
        'reservas_cliente': reservas_cliente
    })

@login_required
def guardar_pqrs(request):
    if request.method == 'POST':
        form = PqrsForm(request.POST, user=request.user)

        if form.is_valid():
            # 1. Guardar la PQRS principal
            nueva_pqrs = form.save(commit=False)
            nueva_pqrs.usuario = request.user
            nueva_pqrs.estado = 'abierto'
            nueva_pqrs.save()

            # 2. Obtener la reserva del formulario
            reserva_seleccionada = form.cleaned_data.get('reserva')

            # 3. CREAR EL SEGUIMIENTO ASOCIANDO LA RESERVA EN BD
            Seguimiento.objects.create(
                pqrs=nueva_pqrs,
                usuario=request.user,
                reserva=reserva_seleccionada
            )

            # 4. Mensaje de confirmación
            reserva_txt = f" para la Reserva #{reserva_seleccionada.id}" if reserva_seleccionada else ""
            messages.success(request, f"Tu PQRS ha sido radicada con éxito{reserva_txt}.")
            return redirect('mis_pqrs')
        else:
            messages.error(request, "Por favor verifica los campos del formulario.")

    return redirect('mis_pqrs')

@login_required
def mis_pqrs_view(request):
    solicitudes_usuario = PQRS.objects.filter(usuario=request.user).prefetch_related('seguimientos').order_by('-fecha')
    form = PqrsForm(user=request.user)

    context = {
        'solicitudes': solicitudes_usuario,
        'form': form,
    }
    return render(request, 'admin/pqrs/mis_pqrs.html', context)