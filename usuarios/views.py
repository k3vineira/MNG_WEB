from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required


@login_required
def inicio_usuarios(request):
    context = {
        'titulo': 'Panel de Usuarios',
        'usuario': request.user
    }
    return render(request, 'index-admin.html', context)


def login_view(request):
    if request.user.is_authenticated:
        return redirect('usuarios:inicio')

    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(
                username=username,
                password=password
            )
            if user is not None:
                auth_login(request, user)
                messages.success(
                    request,
                    f"¡Bienvenido de nuevo, {user.username}!"
                )
                return redirect('usuarios:inicio')
    else:
        form = AuthenticationForm()
    return render(
        request,
        'authentication/login.html',
        {'form': form}
    )


def registro_view(request):
    return render(
        request,
        'authentication/registro.html'
    )


def terminos_view(request):
    return render(
        request,
        'authentication/terminos.html'
    )