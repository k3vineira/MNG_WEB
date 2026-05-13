from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from .models import Promocion

@user_passes_test(lambda u: u.is_staff)
def promociones_gestion(request):
    """Lista todas las promociones en el dashboard."""
    promociones = Promocion.objects.all()
    return render(request, 'promociones_gestion.html', {'promociones': promociones})

@user_passes_test(lambda u: u.is_staff)
def guardar_promocion(request):
    """Maneja la creación y edición de banners en una sola función (DRY)."""
    if request.method == 'POST':
        promo_id = request.POST.get('promocion_id')
        
        # Si hay ID, editamos; si no, creamos uno nuevo
        if promo_id:
            promocion = get_object_or_404(Promocion, id=promo_id)
        else:
            promocion = Promocion()

        # Asignación de campos
        promocion.nombre = request.POST.get('nombre')
        promocion.descripcion = request.POST.get('descripcion')
        promocion.enlace = request.POST.get('enlace')
        promocion.porcentaje_descuento = request.POST.get('porcentaje_descuento', 0)
        promocion.prioridad = request.POST.get('prioridad', 0)
        promocion.activo = 'activo' in request.POST
        promocion.solo_usuarios = request.POST.get('solo_usuarios') == 'True'
        
        # Manejo de fechas opcionales
        f_inicio = request.POST.get('fecha_inicio')
        f_fin = request.POST.get('fecha_fin')
        promocion.fecha_inicio = f_inicio if f_inicio else None
        promocion.fecha_fin = f_fin if f_fin else None

        # Manejo de imagen
        if 'imagen' in request.FILES:
            promocion.imagen = request.FILES['imagen']

        promocion.save()
        messages.success(request, "Banner publicitario guardado correctamente.")
        
    return redirect('promociones_gestion')

@user_passes_test(lambda u: u.is_staff)
def eliminar_promocion(request, id):
    """Elimina una promoción."""
    promocion = get_object_or_404(Promocion, id=id)
    promocion.delete()
    messages.warning(request, "La promoción ha sido eliminada.")
    return redirect('promociones_gestion')
