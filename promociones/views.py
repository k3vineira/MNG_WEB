from django.shortcuts import render

# Create your views here.
def gestion_promociones(request):
    return render(request, 'promociones_gestion.html')

