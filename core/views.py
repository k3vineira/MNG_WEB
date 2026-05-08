from django import forms
from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def inicio(request):
    # Aquí va la lógica de tu dashboard de Monagua
    return render(request, 'inicio.html') 
