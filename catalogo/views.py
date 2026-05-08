from django.shortcuts import render

def inicio(request):
    return render(request, 'public/inicio.html', {
        'paquetes_destacados': [],
        'promociones_activas': [],
        'blog_reciente':       [],
    })