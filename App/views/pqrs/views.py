from django.shortcuts import render
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from App.models import PQRS, Seguimiento
from App.forms.pqrs.forms import PqrsForm
from django.views.generic import ListView
from django.db.models import Count, Q
from App.models import *
from core.decoradores import requiere_autenticacion


def pqrs(request):
    pqrs = PQRS.objects.all()
    form = PqrsForm()
    context = {'pqrs': pqrs, 'form': form}
    return render(request, 'admin/pqrs/pqrs.html', context)


class PQRSListView(ListView):
    model = PQRS
    template_name = 'admin/pqrs/pqrs_admin.html'
    context_object_name = 'todas_las_pqrs'

    def get_queryset(self):
        return PQRS.objects.all().order_by('-fecha')

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
        
        if respuesta_texto:
            seguimiento_creado = Seguimiento.objects.create(
                pqrs=pqr,
                usuario=request.user,
                respuesta=respuesta_texto
            )
            
            pqr.estado = 'cerrado'
            pqr.save()

            from App.utils import registrar_bitacora
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

    return render(request, 'admin/contestar_pqrs.html', {'pqr': pqr})

def guardar_pqrs(request):
    if request.method == 'POST':
        form = PqrsForm(request.POST)
        if form.is_valid():
            nueva_pqrs = form.save(commit=False)
            
            if request.user.is_authenticated:
                nueva_pqrs.usuario = request.user
            else:
                nueva_pqrs.usuario = None

            nueva_pqrs.estado = 'abierto'
            nueva_pqrs.save()

            messages.success(request, "Tu PQRS ha sido radicada con éxito.")
            return redirect('mis_pqrs')
        else:
            print(f"--- ERRORES DEL FORMULARIO: {form.errors} ---")
            messages.error(request, "Por favor verifica los campos del formulario.")

    return redirect('admin/pqrs/mis_pqrs')

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