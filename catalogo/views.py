from django.shortcuts import render
from .models import Paquete
from promociones.models import Promocion
from comunidad.models import BlogNoticia  # ajusta según tus nombres de modelo

def inicio(request):
    context = {
        'paquetes_destacados': Paquete.objects.filter(activo=True).order_by('-id')[:3],
        'promociones_activas': Promocion.objects.filter(activa=True)[:3],
        'blog_reciente':       BlogNoticia.objects.order_by('-fecha_publicacion')[:3],
    }
    return render(request, 'public/index.html', context)

def destinos(request):
    return render(request, 'public/destinos.html')

def paquetes(request):
    return render(request, 'public/paquetes.html')

def detalle_paquete(request, pk):
    return render(request, 'public/detalle_paquete.html')

def promociones(request):
    return render(request, 'public/promociones.html')

def blog(request):
    return render(request, 'public/blog.html')

def blog_detalle(request, pk):
    return render(request, 'public/blog_detalle.html')

def nosotros(request):
    return render(request, 'public/nosotros.html')

def terminos(request):
    return render(request, 'public/terminos.html')