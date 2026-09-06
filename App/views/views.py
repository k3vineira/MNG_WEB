from django.shortcuts import render
from App.views.paquete.views import tours

def index(request):
    return render(request, 'index.html')
