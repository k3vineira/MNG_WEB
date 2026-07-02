from django.test import TestCase
from django.contrib.auth import authenticate
from usuarios.models import Usuario
from autenticacion.forms import RegistroForm

class AuthenticationAndEmailUniquenessTests(TestCase):
    def setUp(self):
        """
        setUp.
        
        :return: Respuesta de la función.
        """
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
        self.assertIn('registro/otp', response.url)

        # Obtener el OTP de la sesión
        session = self.client.session
        otp = session.get('registro_otp')
        self.assertIsNotNone(otp)

        # Confirmar el OTP
        response_otp = self.client.post(reverse('registro_otp'), data={'otp': otp})
        self.assertEqual(response_otp.status_code, 302)

        # Verificar que el usuario fue creado en la base de datos
        self.assertTrue(Usuario.objects.filter(username='viewuser').exists())

    def test_custom_set_password_form_same_password(self):
        """Probar que el formulario CustomSetPasswordForm falla si se ingresa la contraseña actual."""
        from autenticacion.forms import CustomSetPasswordForm
        form_data = {
            'new_password1': 'securepassword123',
            'new_password2': 'securepassword123',
        }
        form = CustomSetPasswordForm(user=self.user, data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertEqual(
            form.errors['__all__'][0],
            "La nueva contraseña no puede ser igual a la anterior. Por favor, elige una diferente."
        )

    def test_custom_set_password_form_success(self):
        """Probar que el formulario guarda y cambia la contraseña correctamente en la base de datos."""
        from autenticacion.forms import CustomSetPasswordForm
        form_data = {
            'new_password1': 'newsecurepassword123',
            'new_password2': 'newsecurepassword123',
        }
        form = CustomSetPasswordForm(user=self.user, data=form_data)
        self.assertTrue(form.is_valid())
        # Guardar la contraseña
        user = form.save()
        # Verificar en base de datos
        self.assertTrue(user.check_password('newsecurepassword123'))
        # Verificar que no es la vieja contraseña
        self.assertFalse(user.check_password('securepassword123'))

    def test_full_password_reset_flow(self):
        """Probar el flujo completo de recuperación de contraseña (solicitud -> OTP -> confirmación -> nueva contraseña -> login)."""
        from django.urls import reverse
        
        # 1. Solicitar recuperación
        solicitud_data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'numero_documento': '123',  # Asumiendo que el usuario de prueba no tiene, modifiquemos el setUp si es necesario
        }
        # Nota: Ajustemos los campos del usuario en el setUp para que coincida con el formulario
        self.user.numero_documento = '123456789'
        self.user.save()
        
        solicitud_data = {
            'username': 'testuser',
            'email': 'testuser@example.com',
            'numero_documento': '123456789',
        }
        
        response = self.client.post(reverse('password_reset'), data=solicitud_data)
        self.assertEqual(response.status_code, 302) # Redirige a OTP
        
        # Obtener el OTP de la sesión
        session = self.client.session
        otp = session.get('reset_otp')
        self.assertIsNotNone(otp)
        
        # 2. Verificar OTP
        response = self.client.post(reverse('password_reset_otp'), data={'otp': otp})
        self.assertEqual(response.status_code, 302) # Redirige a done
        
        # Verificar que se redirige a password_reset_done
        redirect_url = response.url
        self.assertIn('password-reset/done', redirect_url)
        
        # 3. Obtener el enlace del correo electrónico enviado
        from django.core import mail
        self.assertEqual(len(mail.outbox), 2) # 1. OTP, 2. Enlace
        
        email_enlace = mail.outbox[1]
        self.assertIn('Enlace para restablecer tu contraseña', email_enlace.subject)
        
        import re
        match = re.search(r'(http[s]?://[^/]+(/autenticacion/password-reset/confirm/[A-Za-z0-9_\-]+/[A-Za-z0-9_\-]+/))', email_enlace.body)
        self.assertIsNotNone(match, "No se encontró el enlace de confirmación en el correo")
        
        confirm_url = match.group(2) # Obtener solo la ruta relativa
        
        # Acceder a la página de confirmación (GET) para verificar que el link es válido
        response = self.client.get(confirm_url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['validlink'])
        
        # 4. Establecer nueva contraseña (POST)
        nueva_pass_data = {
            'new_password1': 'newsecurepassword123',
            'new_password2': 'newsecurepassword123',
        }
        # Postear a la URL final (la redirigida)
        final_url = response.request['PATH_INFO']
        response = self.client.post(final_url, data=nueva_pass_data)
        self.assertEqual(response.status_code, 302) # Redirige al éxito
        
        # 5. Verificar que la contraseña realmente cambió en la base de datos
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('newsecurepassword123'))
        
        # 6. Intentar iniciar sesión con las nuevas credenciales
        login_data = {
            'username': 'testuser',
            'password': 'newsecurepassword123',
        }
        response = self.client.post(reverse('login'), data=login_data)
        self.assertEqual(response.status_code, 302) # Redirige al panel de inicio del turista u otro
        
        # Verificar que el usuario quedó autenticado en la sesión
        self.assertTrue('_auth_user_id' in self.client.session)
