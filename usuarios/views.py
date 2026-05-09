
from django.shortcuts import render

def inicio_usuarios(request):
   
    context = {
        'titulo': 'Panel de Usuarios'
    }
    
    return render(request, 'index-admin.html', context)