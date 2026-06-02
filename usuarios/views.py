from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from .models import Usuario, Cliente, Comentario
from .forms import RegistroForm, PerfilUsuarioForm


@login_required
def index_turista(request):
    # if request.user.is_staff:
    #     return redirect('dashboard')
    context = {'titulo': 'Bienvenido a Monagua'}
    return render(request, 'index_turista.html', context)


@user_passes_test(lambda u: u.is_staff, login_url='inicio')
def dashboard_admin(request):
    from reservas.models import Reserva, Cancelacion
    from catalogo.models import Paquete
    from django.db.models import Sum, Count, Avg
    from django.utils.timesince import timesince
    from datetime import timedelta

    hoy = timezone.now().date()
    anio_actual = hoy.year

    try:
        total_usuarios = Usuario.objects.filter(is_staff=False).count()
    except:
        total_usuarios = 0

    try:
        total_tours = Paquete.objects.filter(estado=True).count()
    except:
        total_tours = 0

    total_reservas = total_ventas = reservas_confirmadas = 0
    reservas_pendientes = reservas_canceladas = tasa_confirmacion = 0
    ingreso_por_reserva = cancelaciones_hoy = 0
    total_pagos_rechazados = cancelaciones_pendientes = cancelaciones_rechazadas = 0
    valoracion_promedio = 0.0
    ingresos_mensuales = [0] * 12
    reservas_semana = [0] * 7
    tours_populares = []
    max_reservas = 1
    actividad_reciente = []

    try:
        from reservas.models import Reserva, Cancelacion
        total_reservas = Reserva.objects.count()
        try:
            total_ventas = Reserva.objects.filter(
                estado='confirmada'
            ).aggregate(total=Sum('monto_total'))['total'] or 0
            reservas_confirmadas = Reserva.objects.filter(estado='confirmada').count()
            reservas_pendientes  = Reserva.objects.filter(estado='pendiente').count()
            reservas_canceladas  = Reserva.objects.filter(estado='cancelada').count()
            if total_reservas > 0:
                tasa_confirmacion = round((reservas_confirmadas / total_reservas) * 100)
            if reservas_confirmadas > 0:
                ingreso_por_reserva = round(total_ventas / reservas_confirmadas)
            for i, mes in enumerate(range(1, 13)):
                total_mes = Reserva.objects.filter(
                    estado='confirmada', fecha__year=anio_actual, fecha__month=mes
                ).aggregate(total=Sum('monto_total'))['total'] or 0
                ingresos_mensuales[i] = float(total_mes)
            
            from pagos.models import ComprobantePago
            total_pagos_rechazados = ComprobantePago.objects.filter(estado='rechazado').count()
            cancelaciones_pendientes = Cancelacion.objects.filter(estado='revision').count()
            cancelaciones_rechazadas = Cancelacion.objects.filter(estado='rechazada').count()
            
            from .models import Comentario
            valoracion_promedio = round(Comentario.objects.filter(visible=True).aggregate(promedio=Avg('valoracion'))['promedio'] or 0.0, 1)
        except Exception as e:
            print(f"[Dashboard] Error: {e}")
        try:
            from datetime import timedelta
            for i, dias in enumerate(range(6, -1, -1)):
                dia = hoy - timedelta(days=dias)
                reservas_semana[i] = Reserva.objects.filter(fecha=dia).count()
        except:
            pass
        try:
            cancelaciones_hoy = Cancelacion.objects.filter(reserva__fecha=hoy).count()
        except:
            pass
        try:
            tours_populares = list(Paquete.objects.annotate(
                numero_reservas=Count('reserva')
            ).order_by('-numero_reservas')[:5])
            max_reservas = tours_populares[0].numero_reservas if tours_populares and tours_populares[0].numero_reservas > 0 else 1
        except:
            pass
        try:
            ultimas = Reserva.objects.select_related('usuario', 'paquete').order_by('-id')[:8]
            for r in ultimas:
                nombre = r.usuario.get_full_name() or r.usuario.username
                try:
                    estado_txt = r.get_estado_display()
                except:
                    estado_txt = 'Sin estado'
                actividad_reciente.append({
                    'texto': f"{nombre} reservó '{r.paquete.nombre}' — {estado_txt}",
                    'tiempo': timesince(r.fecha) + ' atrás',
                })
        except:
            pass
    except Exception as e:
        print(f"[Dashboard] Error importando Reserva: {e}")

    context = {
        'titulo':               'Tablero de Rendimiento',
        'total_ventas':         total_ventas,
        'total_usuarios':       total_usuarios,
        'total_reservas':       total_reservas,
        'total_tours':          total_tours,
        'total_promociones':    0,
        'ingresos_mensuales':   ingresos_mensuales,
        'reservas_confirmadas': reservas_confirmadas,
        'reservas_pendientes':  reservas_pendientes,
        'reservas_canceladas':  reservas_canceladas,
        'reservas_semana':      reservas_semana,
        'tasa_confirmacion':    tasa_confirmacion,
        'valoracion_promedio':  valoracion_promedio,
        'ingreso_por_reserva':  ingreso_por_reserva,
        'cancelaciones_hoy':    cancelaciones_hoy,
        'total_pagos_rechazados': total_pagos_rechazados,
        'cancelaciones_pendientes': cancelaciones_pendientes,
        'cancelaciones_rechazadas': cancelaciones_rechazadas,
        'tours_populares':      tours_populares,
        'max_reservas':         max_reservas,
        'actividad_reciente':   actividad_reciente,
    }
    return render(request, 'admin/index-admin.html', context)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('inicio')
    if request.method == 'POST':
        data = request.POST.copy()
        username_input = data.get('username')
        if username_input and '@' in username_input:
            user_obj = Usuario.objects.filter(email=username_input).first()
            if user_obj:
                data['username'] = user_obj.username
        form = AuthenticationForm(request, data=data)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                auth_login(request, user)
                messages.success(request, f"¡Bienvenido de nuevo, {user.username}!")
                # Redirect tourists to their landing page after login
                if hasattr(user, 'rol') and user.rol == Usuario.Roles.CLIENTE:
                    return redirect('index_turista')
                next_url = request.GET.get('next')
                if next_url:
                    paquete_id = request.GET.get('paquete_id')
                    if paquete_id:
                        next_url = f"{next_url}?paquete_id={paquete_id}"
                    return redirect(next_url)
                return redirect('inicio')
    else:
        form = AuthenticationForm()
    return render(request, 'authentication/login.html', {'form': form})



def logout_view(request):
    auth_logout(request)
    messages.info(request, "Has cerrado sesión exitosamente.")
    return redirect('login')


def registro_view(request):
    if request.user.is_authenticated:
        return redirect('inicio')
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.rol = Usuario.Roles.CLIENTE
            pais = request.POST.get('pais', '')
            ciudad = request.POST.get('ciudad', '')
            if pais and ciudad:
                user.residencia = f"{ciudad}, {pais}"
            user.save()
            Cliente.objects.create(usuario=user, pais=pais, ciudad=ciudad)
            # Auto-login the new tourist user
            from django.contrib.auth import login as auth_login
            auth_login(request, user)
            messages.success(request, "¡Registro exitoso! Bienvenido.")
            return redirect('index_turista')
        else:
            messages.error(request, "Hubo un error en el registro. Por favor, revisa los datos.")
    else:
        form = RegistroForm()
    return render(request, 'authentication/registro.html', {'form': form})


def terminos_view(request):
    return render(request, 'public/terminos.html')


def nosotros_view(request):
    return render(request, 'public/nosotros.html')


@login_required
def perfil_view(request):
    user = request.user
    if request.method == 'POST':
        if 'imagen_perfil' in request.FILES:
            user.imagen_perfil = request.FILES['imagen_perfil']
            user.save()
            messages.success(request, "¡Foto de perfil actualizada con éxito!")
            return redirect('detalles')
            
        elif request.POST.get('editar_perfil') == '1':
            form = PerfilUsuarioForm(request.POST, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, '¡Información actualizada correctamente!')
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field.replace('_', ' ').capitalize()}: {error}")
        return redirect('detalles')
    return render(request, 'private/perfil_turista.html')


@user_passes_test(lambda u: u.is_staff)
def gestion_guias(request, id=None):
    all_users = Usuario.objects.all().order_by('-date_joined')
    guias     = Usuario.objects.filter(es_guia=True)
    guia_sel  = get_object_or_404(Usuario, id=id) if id else None
    context = {
        'fecha':                 timezone.now().strftime('%d %b, %Y'),
        'guias':                 guias,
        'total_guias':           guias.count(),
        'total_guias_activos':   guias.filter(is_active=True).count(),
        'guias_asignados':       0,
        'total_guias_inactivos': guias.filter(is_active=False).count(),
        'all_users':             all_users,
        'total_users':           all_users.count(),
        'guia_sel':              guia_sel,
    }
    return render(request, 'admin/index-guias.html', context)


@user_passes_test(lambda u: u.is_staff)
def asignar_rol_guia(request, user_id):
    if request.method == 'POST':
        user_obj = get_object_or_404(Usuario, id=user_id)
        user_obj.es_guia = not user_obj.es_guia
        user_obj.save()
        accion = "asignado como" if user_obj.es_guia else "removido de"
        messages.success(request, f"Usuario {user_obj.username} {accion} guía.")
    return redirect('gestion_guias')


@user_passes_test(lambda u: u.is_staff)
def guias_baja_reactivar(request, id, estado):
    if request.method == 'POST':
        guia = get_object_or_404(Usuario, id=id)
        guia.is_active = (estado == 'activar')
        guia.save()
        msg = "reactivado" if guia.is_active else "dado de baja"
        messages.info(request, f"Guía {guia.first_name} {msg} exitosamente.")
    return redirect('gestion_guias')


@user_passes_test(lambda u: u.is_staff)
def guias_guardar(request):
    if request.method == 'POST':
        messages.success(request, "Datos del guía guardados correctamente.")
    return redirect('gestion_guias')


# ── Comentarios ──────────────────────────────────────────────────────────────

@login_required
def enviar_comentario(request):
    from catalogo.models import Paquete
    if request.method == 'POST':
        tipo       = request.POST.get('tipo', 'experiencia')
        titulo     = request.POST.get('titulo', '').strip()
        mensaje    = request.POST.get('mensaje', '').strip()
        try:
            valoracion = max(1, min(5, int(request.POST.get('valoracion', 5))))
        except (ValueError, TypeError):
            valoracion = 5

        paquete = None
        if tipo.startswith('paquete_'):
            try:
                paquete_id = int(tipo.split('_')[1])
                paquete = Paquete.objects.filter(id=paquete_id).first()
                tipo = 'experiencia'
            except (ValueError, IndexError):
                pass

        if titulo and mensaje:
            Comentario.objects.create(
                usuario=request.user,
                tipo=tipo,
                titulo=titulo,
                mensaje=mensaje,
                valoracion=valoracion,
                paquete=paquete,
            )
            messages.success(request, '¡Tu comentario fue enviado correctamente!')
        else:
            messages.error(request, 'Por favor completa todos los campos.')
        return redirect('mis_resenas')

    mis_comentarios = Comentario.objects.filter(
        usuario=request.user
    ).select_related('paquete').order_by('-fecha_creacion')[:5]

    comentarios_publicos = Comentario.objects.filter(
        visible=True
    ).select_related('usuario', 'paquete').exclude(usuario=request.user).order_by('-fecha_creacion')[:10]

    paquetes_activos = Paquete.objects.filter(estado=True)
    context = {
        'mis_comentarios':      mis_comentarios,
        'comentarios_publicos': comentarios_publicos,
        'paquetes_activos':     paquetes_activos,
    }
    return render(request, 'private/comentarios.html', context)


@user_passes_test(lambda u: u.is_staff)
def listar_comentarios(request):
    from django.db.models import Avg
    tipo_filtro       = request.GET.get('tipo', '')
    valoracion_filtro = request.GET.get('valoracion', '')
    comentarios = Comentario.objects.select_related('usuario', 'paquete').all()
    if tipo_filtro:
        comentarios = comentarios.filter(tipo=tipo_filtro)
    if valoracion_filtro:
        comentarios = comentarios.filter(valoracion=valoracion_filtro)
    total          = comentarios.count()
    total_visibles = comentarios.filter(visible=True).count()
    agg = comentarios.aggregate(avg=Avg('valoracion'))
    promedio = round(agg['avg'] or 0, 1)
    context = {
        'comentarios':        comentarios,
        'total':              total,
        'total_visibles':     total_visibles,
        'promedio':           promedio,
        'tipo_filtro':        tipo_filtro,
        'valoracion_filtro':  valoracion_filtro,
    }
    return render(request, 'admin/comentarios.html', context)


@user_passes_test(lambda u: u.is_staff)
def toggle_visible(request, pk):
    if request.method == 'POST':
        comentario = get_object_or_404(Comentario, pk=pk)
        comentario.visible = not comentario.visible
        comentario.save()
        estado = 'visible' if comentario.visible else 'oculto'
        messages.success(request, f'Comentario marcado como {estado}.')
    return redirect('listar_comentarios')

@login_required
def mis_resenas_view(request):
    from django.db.models import Avg, Count
    from catalogo.models import Paquete

    # ── POST: crear nueva reseña ─────────────────────────────────────────
    if request.method == 'POST':
        tipo       = request.POST.get('tipo', 'experiencia')
        titulo     = request.POST.get('titulo', '').strip()
        mensaje    = request.POST.get('mensaje', '').strip()
        valoracion = request.POST.get('valoracion', '5')
        try:
            valoracion = max(1, min(5, int(valoracion)))
        except (ValueError, TypeError):
            valoracion = 5

        paquete = None
        if tipo.startswith('paquete_'):
            try:
                paquete_id = int(tipo.split('_')[1])
                paquete = Paquete.objects.filter(id=paquete_id).first()
                tipo = 'experiencia'
            except (ValueError, IndexError):
                pass

        if titulo and mensaje:
            Comentario.objects.create(
                usuario=request.user,
                tipo=tipo,
                titulo=titulo,
                mensaje=mensaje,
                valoracion=valoracion,
                paquete=paquete,
            )
            messages.success(request, '¡Tu reseña fue enviada correctamente!')
        else:
            messages.error(request, 'Por favor completa todos los campos.')
        return redirect('mis_resenas')

    # ── GET: mostrar reseñas ─────────────────────────────────────────────
    mis_resenas = Comentario.objects.filter(
        usuario=request.user
    ).select_related('paquete').order_by('-fecha_creacion')[:10]

    resenas_publicas = Comentario.objects.filter(
        visible=True
    ).select_related('usuario', 'paquete').order_by('-fecha_creacion')[:20]

    # Estadísticas
    todas = Comentario.objects.filter(visible=True)
    agg = todas.aggregate(total=Count('id'), promedio=Avg('valoracion'))
    stats = {
        'total':    agg['total'] or 0,
        'promedio': round(agg['promedio'] or 0, 1),
    }

    # Distribución de estrellas (1-5)
    distribucion = {}
    if stats['total'] > 0:
        dist_qs = todas.values('valoracion').annotate(cnt=Count('id'))
        for row in dist_qs:
            distribucion[row['valoracion']] = row['cnt']

    paquetes_activos = Paquete.objects.filter(estado=True)

    context = {
        'mis_resenas':       mis_resenas,
        'resenas_publicas':  resenas_publicas,
        'stats':             stats,
        'distribucion':      distribucion,
        'paquetes_activos':  paquetes_activos,
    }
    return render(request, 'private/resenas.html', context)

@login_required
def estadisticas_usuario(request):
    if request.user.is_staff:
        return redirect('dashboard')
        
    from reservas.models import Reserva
    from pagos.models import ComprobantePago
    from comunidad.models import PQRS
    from .models import Comentario, Cliente
    from django.db.models import Sum
    
    total_reservas = Reserva.objects.filter(usuario=request.user).count()
    reservas_confirmadas = Reserva.objects.filter(usuario=request.user, estado='confirmada').count()
    reservas_pendientes  = Reserva.objects.filter(usuario=request.user, estado='pendiente').count()
    reservas_canceladas  = Reserva.objects.filter(usuario=request.user, estado='cancelada').count()
    
    total_invertido = ComprobantePago.objects.filter(
        usuario=request.user, estado='aprobado'
    ).aggregate(total=Sum('monto'))['total'] or 0.0
    
    total_comentarios = Comentario.objects.filter(usuario=request.user).count()

    # Safely query PQRS — only if the user has a Cliente profile
    total_pqrs = 0
    try:
        cliente_obj = Cliente.objects.get(usuario=request.user)
        total_pqrs = PQRS.objects.filter(cliente=cliente_obj).count()
    except Cliente.DoesNotExist:
        pass
    
    context = {
        'total_reservas':       total_reservas,
        'reservas_confirmadas': reservas_confirmadas,
        'reservas_pendientes':  reservas_pendientes,
        'reservas_canceladas':  reservas_canceladas,
        'total_invertido':      total_invertido,
        'total_comentarios':    total_comentarios,
        'total_pqrs':           total_pqrs,
    }
    return render(request, 'private/estadisticas.html', context)


@login_required
def dashboard_turista(request):
    if request.user.is_staff:
        return redirect('dashboard')

    from reservas.models import Reserva
    from pagos.models import ComprobantePago
    from comunidad.models import PQRS
    from .models import Comentario, Cliente
    from django.db.models import Sum

    total_reservas = Reserva.objects.filter(usuario=request.user).count()
    reservas_confirmadas = Reserva.objects.filter(usuario=request.user, estado='confirmada').count()
    reservas_pendientes  = Reserva.objects.filter(usuario=request.user, estado='pendiente').count()
    reservas_canceladas  = Reserva.objects.filter(usuario=request.user, estado='cancelada').count()

    tasa_confirmacion = 0
    if total_reservas > 0:
        tasa_confirmacion = round((reservas_confirmadas / total_reservas) * 100)

    total_invertido = ComprobantePago.objects.filter(
        usuario=request.user, estado='aprobado'
    ).aggregate(total=Sum('monto'))['total'] or 0.0

    total_comentarios = Comentario.objects.filter(usuario=request.user).count()

    total_pqrs = 0
    try:
        cliente_obj = Cliente.objects.get(usuario=request.user)
        total_pqrs = PQRS.objects.filter(cliente=cliente_obj).count()
    except Cliente.DoesNotExist:
        pass

    ultimas_reservas = Reserva.objects.filter(
        usuario=request.user
    ).select_related('paquete').order_by('-id')[:5]

    context = {
        'total_reservas':       total_reservas,
        'reservas_confirmadas': reservas_confirmadas,
        'reservas_pendientes':  reservas_pendientes,
        'reservas_canceladas':  reservas_canceladas,
        'tasa_confirmacion':    tasa_confirmacion,
        'total_invertido':      total_invertido,
        'total_comentarios':    total_comentarios,
        'total_pqrs':           total_pqrs,
        'ultimas_reservas':     ultimas_reservas,
    }
    return render(request, 'private/dashboard_turista.html', context)