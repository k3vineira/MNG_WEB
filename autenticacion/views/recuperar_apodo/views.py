from django.shortcuts import render
from django.contrib import messages
from App.models import Usuario


def recuperar_apodo_vista(request):
    """
    Permite al usuario recuperar su nombre de usuario (apodo) verificando
    su correo electrónico y/o número de documento en la base de datos.
    """
    context = {}

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        numero_documento = request.POST.get('numero_documento', '').strip()

        if email or numero_documento:
            usuario = None
            try:
                if email and numero_documento:
                    usuario = Usuario.objects.get(
                        email__iexact=email,
                        numero_documento=numero_documento
                    )
                elif email:
                    usuario = Usuario.objects.get(email__iexact=email)
                else:
                    usuario = Usuario.objects.get(numero_documento=numero_documento)

                context['apodo_encontrado'] = usuario.username
                messages.success(request, f"Hemos encontrado tu cuenta: {usuario.username}")
            except Usuario.DoesNotExist:
                messages.error(request, 'No encontramos ninguna cuenta activa con los datos proporcionados.')
        else:
            messages.error(request, 'Por favor ingresa tu correo electrónico o tu número de documento.')

    return render(request, 'autenticacion/recuperar_apodo.html', context)
