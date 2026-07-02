"""
Backends de autenticación personalizados para el proyecto.
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Backend de autenticación personalizado que permite iniciar sesión
    utilizando el nombre de usuario (apodo) o el correo electrónico.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Autentica a un usuario usando su correo electrónico o nombre de usuario.

        Args:
            request (HttpRequest): Objeto de solicitud HTTP actual.
            username (str, optional): Nombre de usuario o correo electrónico.
            password (str, optional): Contraseña del usuario.
            **kwargs: Parámetros adicionales.

        Returns:
            User: El objeto del usuario autenticado si es exitoso, None en caso contrario.
        """
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        
        try:
            # Buscar por username (apodo) o por correo electrónico (email), ignorando mayúsculas/minúsculas
            user = UserModel.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        except UserModel.DoesNotExist:
            # Ejecutar el hasher de contraseñas para mitigar ataques de temporización
            UserModel().set_password(password)
            return None
        
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

