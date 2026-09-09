from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from App.models import Usuario


from django.contrib import messages

@login_required
def panel_rapido_view(request):
    if not request.user.es_turista:
        if request.user.is_staff or request.user.rol == Usuario.Roles.ADMIN:
            return redirect('dashboard_admin')
        return redirect('index')

    return render(request, 'partials/panel_rapido.html')


@login_required
def perfil_turista_view(request):
    """Renderiza y gestiona la actualización del perfil del turista/cliente."""
    user = request.user
    if request.method == 'POST' and request.POST.get('editar_perfil') == '1':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        imagen_perfil = request.FILES.get('imagen_perfil')

        if first_name:
            user.first_name = first_name
        if last_name:
            user.last_name = last_name
        if telefono:
            user.telefono = telefono
        if imagen_perfil:
            user.imagen_perfil = imagen_perfil

        user.save()
        messages.success(request, 'Tu perfil ha sido actualizado correctamente.')
        return redirect('perfil_detalles')

    return render(request, 'usuario/perfil_turista.html', {'user': user})

  