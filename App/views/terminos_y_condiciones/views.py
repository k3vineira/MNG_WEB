from django.shortcuts import render


def terminos_view(request):
    """Renderiza la plantilla de Términos y Condiciones."""
    return render(request, 'usuario/terminos.html', {
        'titulo': 'Términos y Condiciones — Monagua'
    })


def nosotros_view(request):
    """Renderiza la plantilla de información corporativa Sobre Nosotros."""
    return render(request, 'nosotros.html', {
        'titulo': 'Sobre Nosotros — Monagua'
    })