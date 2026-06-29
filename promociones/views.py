from django.shortcuts import render
from .models import Promocion

def gestion_promociones(request):
    promociones_activas = Promocion.objects.filter(activa=True)
    context = {
        'promociones': promociones_activas,
        'titulo': 'Gestión de Promociones — Monagua'
    }
    return render(request, 'promociones/promociones.html', context)
