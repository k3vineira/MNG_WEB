from django.http import JsonResponse
from django.views.decorators.http import require_GET
from App.models import Usuario


@require_GET
def verificar_campo_ajax(request):
    """
    Verifica en tiempo real si un dato (username, email, numero_documento, telefono)
    ya existe en la base de datos para la validación interactiva del registro.
    """
    campo = request.GET.get('campo', '').strip()
    valor = request.GET.get('valor', '').strip()

    if not campo or not valor:
        return JsonResponse({'error': 'Parámetros inválidos'}, status=400)

    disponible = True
    mensaje = ""

    if campo == 'username':
        exists = Usuario.objects.filter(username__iexact=valor).exists()
        if exists:
            disponible = False
            mensaje = "Este nombre de usuario ya está registrado."

    elif campo == 'email':
        exists = Usuario.objects.filter(email__iexact=valor).exists()
        if exists:
            disponible = False
            mensaje = "Este correo electrónico ya está registrado."

    elif campo == 'numero_documento':
        exists = Usuario.objects.filter(numero_documento=valor).exists()
        if exists:
            disponible = False
            mensaje = "Este número de documento ya está registrado."

    elif campo == 'telefono':
        exists = Usuario.objects.filter(telefono=valor).exists()
        if exists:
            disponible = False
            mensaje = "Este número de teléfono ya está registrado."

    return JsonResponse({
        'disponible': disponible,
        'mensaje': mensaje
    })
