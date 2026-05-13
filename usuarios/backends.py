from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

class EmailOrUsernameModelBackend(ModelBackend):
    """
    Backend de autenticación personalizado que permite a los usuarios
    iniciar sesión utilizando su nombre de usuario o su correo electrónico.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)

        try:
            # Busca al usuario por username o email (sin distinguir mayúsculas/minúsculas)
            user = UserModel.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        except (UserModel.DoesNotExist, UserModel.MultipleObjectsReturned):
            # Mitigación de ataques de tiempo (timing attacks)
            UserModel().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None