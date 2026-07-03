"""
Vistas principales del núcleo de la aplicación, incluyendo la página de inicio.
"""

from django.shortcuts import render


def inicio(request):
    """
    Renderiza la página de inicio pública del sitio Monagua.

    Args:
        request (HttpRequest): Objeto de solicitud HTTP.

    Returns:
        HttpResponse: La página de inicio renderizada.
    """
    context = {'titulo': 'Monagua — Agencia de Viajes y Turismo'}
    return render(request, 'index.html', context)
