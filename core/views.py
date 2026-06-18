from django.shortcuts import render


def inicio(request):
    context = {'titulo': 'Monagua — Agencia de Viajes y Turismo'}
    return render(request, 'index.html', context)
