from django.shortcuts import render

def index(request):
    return render(request, 'index.html')

def tours(request):
    # Cambiamos temporalmente a renderizar destinos.html si no existe Tours.html
    return render(request, 'partials/Tours.html')
