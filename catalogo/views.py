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

