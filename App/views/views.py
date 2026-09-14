from django.shortcuts import render
from App.models import Blog

def index(request):
    blogs = Blog.objects.filter(estado=True).select_related('usuario').order_by('-fecha_publicacion')[:3]
    return render(request, 'index.html', {'blogs': blogs})
