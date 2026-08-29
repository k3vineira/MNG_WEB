from django.contrib.auth.mixins import UserPassesTestMixin

class StaffRequiredMixin(UserPassesTestMixin):
    """
    Mixin para asegurar que el usuario esté autenticado y sea administrador (is_staff o rol ADMIN).
    """
    def test_func(self):
        return self.request.user.is_authenticated and (
            self.request.user.is_staff or getattr(self.request.user, 'rol', None) == 1
        )
