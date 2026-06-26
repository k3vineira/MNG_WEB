from django.test import TestCase
from django.contrib.auth import authenticate
from usuarios.models import Usuario
from usuarios.forms import RegistroForm

class AuthenticationAndEmailUniquenessTests(TestCase):
    def setUp(self):
        # Crear un usuario de prueba
        self.user = Usuario.objects.create_user(
            username='testuser',
            email='testuser@example.com',
            password='securepassword123',
            first_name='Test',
            last_name='User'
        )

    def test_authenticate_by_username(self):
        """Probar autenticación con el nombre de usuario/apodo."""
        user = authenticate(username='testuser', password='securepassword123')
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'testuser')

    def test_authenticate_by_email(self):
        """Probar autenticación con el correo electrónico exacto."""
        user = authenticate(username='testuser@example.com', password='securepassword123')
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'testuser')

    def test_authenticate_by_email_case_insensitive(self):
        """Probar autenticación con el correo en mayúsculas/minúsculas."""
        user = authenticate(username='TESTUSER@EXAMPLE.COM', password='securepassword123')
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'testuser')

    def test_registration_form_unique_email(self):
        """Probar que el formulario de registro falla si el correo ya existe."""
        form_data = {
            'username': 'newuser',
            'email': 'TESTUSER@EXAMPLE.COM',  # Duplicado en diferente caso
            'first_name': 'New',
            'last_name': 'User',
            'tipo_documento': 'CC',
            'numero_documento': '123456789',
            'telefono': '3001234567',
        }
        form = RegistroForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertEqual(
            form.errors['email'][0],
            "Ya existe un usuario registrado con este correo electrónico."
        )

    def test_registration_form_success(self):
        """Probar registro exitoso con un correo nuevo y único."""
        form_data = {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'first_name': 'New',
            'last_name': 'User',
            'tipo_documento': 'CC',
            'numero_documento': '123456789',
            'telefono': '3001234567',
            'password1': 'Newpassword123',
            'password2': 'Newpassword123',
        }
        form = RegistroForm(data=form_data)
        self.assertTrue(form.is_valid())
        user = form.save()
        self.assertEqual(user.username, 'newuser')
        self.assertEqual(user.email, 'newuser@example.com')

    def test_registration_view_success(self):
        """Probar que la vista de registro crea el usuario, inicia sesión y redirige sin errores."""
        from django.urls import reverse
        form_data = {
            'username': 'viewuser',
            'email': 'viewuser@example.com',
            'first_name': 'View',
            'last_name': 'User',
            'tipo_documento': 'CC',
            'numero_documento': '987654321',
            'telefono': '3007654321',
            'password1': 'Viewpassword123',
            'password2': 'Viewpassword123',
        }
        response = self.client.post(reverse('registro'), data=form_data)
        # La vista de registro debe procesar la solicitud con éxito y redirigir
        self.assertEqual(response.status_code, 302)
        
        # Verificar que el usuario fue creado en la base de datos
        self.assertTrue(Usuario.objects.filter(username='viewuser').exists())
