from django.shortcuts import render


def inicio(request):
    return render(request, 'index.html', {'titulo': 'Monagua — Agencia de Viajes y Turismo'})
