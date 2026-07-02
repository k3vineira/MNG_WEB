"""
Pruebas unitarias para la aplicación de autenticación.
"""

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model, authenticate
from django.core import mail
from autenticacion.backends import EmailOrUsernameModelBackend
from autenticacion.forms import RegistroForm, RecuperacionPersonalizadaForm, CustomSetPasswordForm

Usuario = get_user_model()

class AutenticacionBackendTests(TestCase):
    """
    Pruebas para el backend de autenticación personalizado.
    """
    def setUp(self):
        """
        Configura el entorno de prueba creando un usuario de prueba.
        """
        self.user = Usuario.objects.create_user(
            username='authuser',
            email='authuser@example.com',
            password='securepassword123',
            first_name='Auth',
            last_name='User',
            tipo_documento='CC',
            numero_documento='111222333',
            telefono='3111234567'
        )
        self.backend = EmailOrUsernameModelBackend()

    def test_authenticate_by_username_success(self):
        """
        Prueba la autenticación exitosa usando el nombre de usuario.
        """
        user = self.backend.authenticate(None, username='authuser', password='securepassword123')
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'authuser')

    def test_authenticate_by_email_success(self):
        """
        Prueba la autenticación exitosa usando el correo electrónico.
        """
        user = self.backend.authenticate(None, username='authuser@example.com', password='securepassword123')
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'authuser')

    def test_authenticate_by_email_case_insensitive(self):
        """
        Prueba la autenticación exitosa insensible a mayúsculas/minúsculas usando el correo electrónico.
        """
        user = self.backend.authenticate(None, username='AUTHUSER@EXAMPLE.COM', password='securepassword123')
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'authuser')

    def test_authenticate_invalid_password(self):
        """
        Prueba que la autenticación falle con una contraseña incorrecta.
        """
        user = self.backend.authenticate(None, username='authuser', password='wrongpassword')
        self.assertIsNone(user)

    def test_authenticate_nonexistent_user(self):
        """
        Prueba que la autenticación falle con un usuario inexistente.
        """
        user = self.backend.authenticate(None, username='nonexistent', password='securepassword123')
        self.assertIsNone(user)


class AutenticacionFormTests(TestCase):
    """
    Pruebas para los formularios de registro y recuperación de contraseñas.
    """
    def setUp(self):
        """
        Configura el entorno de prueba creando un usuario registrado previamente.
        """
        self.user = Usuario.objects.create_user(
            username='existinguser',
            email='existing@example.com',
            password='password123',
            first_name='Existing',
            last_name='User',
            tipo_documento='CC',
            numero_documento='99999',
            telefono='3000000000'
        )

    def test_registro_form_valid(self):
        """
        Prueba que el formulario de registro sea válido con datos correctos.
        """
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'tipo_documento': 'CC',
            'numero_documento': '88888',
            'telefono': '3001112222',
            'password1': 'Newpass123',
            'password2': 'Newpass123',
        }
        form = RegistroForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors.as_data())

    def test_registro_form_duplicate_document(self):
        """
        Prueba que el formulario de registro invalide un documento duplicado.
        """
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'tipo_documento': 'CC',
            'numero_documento': '99999',  # duplicado
            'telefono': '3001112222',
            'password1': 'Newpass123',
            'password2': 'Newpass123',
        }
        form = RegistroForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('numero_documento', form.errors)

    def test_registro_form_invalid_names(self):
        """
        Prueba que el formulario de registro invalide nombres con caracteres no permitidos.
        """
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New123',  # Inválido, contiene números
            'last_name': 'User',
            'tipo_documento': 'CC',
            'numero_documento': '88888',
            'telefono': '3001112222',
            'password1': 'Newpass123',
            'password2': 'Newpass123',
        }
        form = RegistroForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)

    def test_recuperacion_personalizada_form_valid(self):
        """
        Prueba que el formulario de recuperación sea válido si los datos coinciden con un usuario.
        """
        form_data = {
            'email': 'existing@example.com',
            'username': 'existinguser',
            'numero_documento': '99999'
        }
        form = RecuperacionPersonalizadaForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_recuperacion_personalizada_form_invalid(self):
        """
        Prueba que el formulario de recuperación invalide datos que no coinciden con un usuario.
        """
        form_data = {
            'email': 'existing@example.com',
            'username': 'wronguser',
            'numero_documento': '99999'
        }
        form = RecuperacionPersonalizadaForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_custom_set_password_form_same_password(self):
        """
        Prueba que no se permita usar la misma contraseña anterior al redefinirla.
        """
        form_data = {
            'new_password1': 'password123',
            'new_password2': 'password123'
        }
        form = CustomSetPasswordForm(user=self.user, data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)


class AutenticacionViewsTests(TestCase):
    """
    Pruebas para las vistas asociadas a la autenticación de usuarios.
    """
    def setUp(self):
        """
        Configura el entorno creando un usuario para probar las vistas.
        """
        self.user = Usuario.objects.create_user(
            username='viewuser',
            email='viewuser@example.com',
            password='password123',
            first_name='View',
            last_name='User',
            tipo_documento='CC',
            numero_documento='12345',
            telefono='3221234567'
        )

    def test_login_view_get(self):
        """
        Prueba el acceso GET a la página de inicio de sesión.
        """
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Inicia sesión')

    def test_login_view_post_success(self):
        """
        Prueba el envío POST exitoso para iniciar sesión.
        """
        response = self.client.post(reverse('login'), {
            'username': 'viewuser',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 302)

    def test_logout_view(self):
        """
        Prueba el cierre de sesión de un usuario autenticado.
        """
        self.client.login(username='viewuser', password='password123')
        response = self.client.get(reverse('logout'))
        self.assertEqual(response.status_code, 302)

    def test_recuperar_apodo_view_success(self):
        """
        Prueba la vista de recuperación de apodo con datos correctos.
        """
        response = self.client.post(reverse('recuperar_apodo'), {
            'email': 'viewuser@example.com',
            'numero_documento': '12345'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'viewuser')

    def test_recuperar_apodo_view_fail(self):
        """
        Prueba la vista de recuperación de apodo con datos incorrectos.
        """
        response = self.client.post(reverse('recuperar_apodo'), {
            'email': 'viewuser@example.com',
            'numero_documento': 'wrongdoc'
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No encontramos ninguna cuenta')

