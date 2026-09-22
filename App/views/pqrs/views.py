from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.views.generic import ListView
from django.db.models import Count, Q

from App.models import PQRS, Seguimiento, Reserva
from App.forms.pqrs.forms import PqrsForm
from App.utils import registrar_bitacora, crear_notificacion_sistema


def notificar_admines_pqrs(pqrs):
    """Notifica a todos los administradores cuando llega una nueva PQRS."""
    User = get_user_model()
    admins = User.objects.filter(Q(is_staff=True) | Q(rol=User.Roles.ADMIN)).distinct()

    for admin in admins:
        crear_notificacion_sistema(
            usuario=admin,
            reserva=None,
            mensaje=f"Ha llegado una nueva PQRS #{pqrs.id} con asunto '{pqrs.asunto}'. Revisa la gestión de PQRS.",
            tipo="PQRS",
            prioridad="alta"
        )


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

            if pqr.usuario:
                crear_notificacion_sistema(
                    usuario=pqr.usuario,
                    reserva=reserva_obj,
                    mensaje=f"Tu PQRS #{pqr.id} recibió una respuesta: {respuesta_texto[:200]}.",
                    tipo="PQRS",
                    prioridad="alta"
                )

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

            # 4. Notificación para el usuario que radica la PQRS
            crear_notificacion_sistema(
                usuario=request.user,
                reserva=reserva_seleccionada,
                mensaje=f"Tu PQRS #{nueva_pqrs.id} ha sido radicada correctamente y quedará en revisión.",
                tipo="PQRS",
                prioridad="media"
            )

            # 5. Notificar a administradores de la nueva PQRS
            notificar_admines_pqrs(nueva_pqrs)

            # 6. Mensaje de confirmación
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

from django.http import JsonResponse
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.conf import settings

def pqrs_publica(request):
    """Renderiza el formulario público de PQRS para visitantes anónimos."""
    form = PqrsForm()
    return render(request, 'public/pqrs.html', {'form': form})

def api_guardar_pqrs(request):
    """Recibe la solicitud POST de PQRS, guarda en BD y envía email."""
    if request.method == 'POST':
        # Validación Anti-Spam (Honeypot)
        honeypot = request.POST.get('website', '')
        if honeypot:
            # Es un bot, lo ignoramos devolviendo éxito silencioso
            return JsonResponse({'status': 'success', 'message': 'Recibido'}, status=200)
            
        user = request.user if request.user.is_authenticated else None
        form = PqrsForm(request.POST, user=user)
        
        if form.is_valid():
            nueva_pqrs = form.save(commit=False)
            if user:
                nueva_pqrs.usuario = user
            nueva_pqrs.estado = 'abierto'
            nueva_pqrs.save() # Aquí se generará el radicado
            
            # Asociar reserva si la hay
            reserva_seleccionada = form.cleaned_data.get('reserva')
            if reserva_seleccionada:
                Seguimiento.objects.create(
                    pqrs=nueva_pqrs,
                    usuario=user,
                    reserva=reserva_seleccionada
                )

            # Notificar al usuario que radicó la PQRS si está autenticado
            if user:
                crear_notificacion_sistema(
                    usuario=user,
                    reserva=reserva_seleccionada,
                    mensaje=f"Tu PQRS #{nueva_pqrs.id} ha sido radicada correctamente y quedará en revisión.",
                    tipo="PQRS",
                    prioridad="media"
                )

            # Notificar a los administradores del sistema
            notificar_admines_pqrs(nueva_pqrs)

            # Enviar correo
            destinatario = user.email if user else nueva_pqrs.correo
            nombre_destinatario = user.get_full_name() or user.username if user else nueva_pqrs.nombre_completo
            
            if destinatario:
                html_message = render_to_string('emails/pqrs_radicada.html', {
                    'nombre': nombre_destinatario,
                    'pqrs': nueva_pqrs
                })
                email = EmailMessage(
                    subject=f"Confirmación de Solicitud PQRS - Radicado: {nueva_pqrs.radicado}",
                    body=html_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[destinatario]
                )
                email.content_subtype = "html"
                email.send(fail_silently=True)
                
            return JsonResponse({
                'status': 'success', 
                'radicado': nueva_pqrs.radicado,
                'message': f"Tu solicitud ha sido radicada exitosamente con el número {nueva_pqrs.radicado}."
            })
        else:
            return JsonResponse({
                'status': 'error',
                'errors': form.errors
            }, status=400)
    
    return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)