import json
from django.http import JsonResponse
from App.services.condy_nlp import procesar_mensaje
from django.views.decorators.csrf import ensure_csrf_cookie

@ensure_csrf_cookie
def condy_chat_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            mensaje = data.get('message', '')
            
            if not mensaje:
                return JsonResponse({'error': 'Mensaje vacío'}, status=400)
            
            # Se requiere que las sesiones estén habilitadas en settings.py
            # Si no están habilitadas, request.session fallará.
            resultado = procesar_mensaje(mensaje, request)
            return JsonResponse(resultado)
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Formato JSON inválido'}, status=400)
    
    return JsonResponse({'error': 'Método no permitido'}, status=405)
