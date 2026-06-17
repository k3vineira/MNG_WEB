from django.shortcuts import render

# Create your views here.


def gestion_promociones(request):
    context = {
        'promociones': [],
        'titulo': 'Gestión de Promociones — Monagua'
    }
    return render(request, 'promociones_gestion.html', context)
