from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from App.models import Usuario


@login_required
def panel_rapido_view(request):
    if not request.user.es_turista:
        if request.user.is_staff or request.user.rol == Usuario.Roles.ADMIN:
            return redirect('dashboard_admin')
        return redirect('index')

    return render(request, 'partials/panel_rapido.html')
