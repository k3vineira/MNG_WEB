from django.shortcuts import render


def inicio(request):
    """
    inicio.
    
    :param request: Descripción del parámetro.
    
    :return: Respuesta de la función.
    """
    context = {'titulo': 'Monagua — Agencia de Viajes y Turismo'}
    return render(request, 'index.html', context)
