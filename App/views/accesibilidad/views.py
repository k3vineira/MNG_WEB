import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import ensure_csrf_cookie

@require_POST
def guardar_accesibilidad(request):
    """
    Guarda las preferencias de accesibilidad en la sesión del usuario de forma segura.
    """
    try:
        data = json.loads(request.body)
        # Solo guardamos llaves esperadas para evitar inyección de basura en la sesión
        llaves_esperadas = [
            "bright", "font", "theme", "saturate", "bigCursor", "hlLinks",
            "dyslexic", "spacing", "animations", "focus", "monochrome", "invert"
        ]
        
        ajustes_seguros = {k: data[k] for k in llaves_esperadas if k in data}
        
        # Guardar en sesión
        request.session['a11y_settings'] = ajustes_seguros
        # Asegurar que se marque como modificada
        request.session.modified = True
        
        return JsonResponse({'status': 'ok', 'message': 'Ajustes guardados correctamente'})
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Formato JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
