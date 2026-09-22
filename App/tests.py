from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from App.models import Usuario, Paquete, Reserva, Categoria, Pago
from App.forms.usuario.forms import PerfilTuristaForm
from App.forms.pago.forms import ComprobantePagoForm
from autenticacion.forms import IniciarSesionForm


class SeguridadFormulariosTests(TestCase):
    """
    Pruebas de seguridad contra ataques basados en manipulación del navegador (DevTools / F12):
    - Mass Assignment (Asignación Masiva para escalamiento de privilegios)
    - Parameter Tampering (Manipulación de montos en comprobantes de pago)
    - Bypass de validaciones de cliente (HTML5 required/pattern eliminados en cliente)
    - Carga de archivos con extensiones peligrosas
    """

    def setUp(self):
        self.client = Client()
        self.turista = Usuario.objects.create_user(
            username='turista_test',
            email='turista@monagua.com',
            password='Password123#',
            first_name='Carlos',
            last_name='Perez',
            rol=Usuario.Roles.CLIENTE,
            is_staff=False,
            is_superuser=False
        )
        self.categoria = Categoria.objects.create(nombre='Aventura')
        self.paquete = Paquete.objects.create(
            nombre='Tour Laguna Negra',
            descripcion='Aventura ecológica',
            categoria=self.categoria,
            punto_encuentro='Plaza de Mongua',
            hora_encuentro='08:00:00',
            dias_duracion=1,
            noches_duracion=1,
            imagen=SimpleUploadedFile('test.jpg', b'contenido_imagen', content_type='image/jpeg')
        )
        self.reserva = Reserva.objects.create(
            usuario=self.turista,
            paquete=self.paquete,
            monto_total=Decimal('350000.00'),
            numero_adultos=2,
            numero_menores=0,
            estado_reserva='pendiente'
        )

    def test_perfil_mass_assignment_protection(self):
        """
        Verifica que si un usuario inyecta campos como 'rol', 'is_staff' o 'is_superuser'
        desde el inspector del navegador, estos sean ignorados y sus privilegios no se eleven.
        """
        self.client.force_login(self.turista)
        payload = {
            'editar_perfil': '1',
            'first_name': 'Carlos Modificado',
            'last_name': 'Perez Modificado',
            'telefono': '3109876543',
            'residencia': 'Mongua',
            # Campos maliciosos inyectados en HTML:
            'rol': Usuario.Roles.ADMIN,
            'is_staff': 'True',
            'is_superuser': 'True',
        }

        response = self.client.post(reverse('perfil_detalles'), data=payload)
        self.assertEqual(response.status_code, 302)

        self.turista.refresh_from_db()
        self.assertEqual(self.turista.first_name, 'Carlos Modificado')
        # Deben permanecer intactos:
        self.assertEqual(self.turista.rol, Usuario.Roles.CLIENTE)
        self.assertFalse(self.turista.is_staff)
        self.assertFalse(self.turista.is_superuser)

    def test_perfil_validation_rejects_invalid_chars(self):
        """
        Verifica que el servidor rechaza nombres con caracteres no permitidos (ej. scripts o números),
        incluso si el atacante borró el atributo 'pattern' del HTML en el navegador.
        """
        form = PerfilTuristaForm(data={
            'first_name': 'Carlos123<script>',
            'last_name': 'Perez',
            'telefono': '3001234567'
        })
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)

    def test_pago_parameter_tampering_protection(self):
        """
        Verifica que si un usuario manipula el HTML de la vista de pagos para enviar 'monto=100'
        o un estado 'aprobado', el servidor ignora esos datos y asigna el monto exacto de la reserva
        en estado 'pendiente'.
        """
        self.client.force_login(self.turista)
        # Bytes de una imagen GIF 1x1 válida compatible con Pillow/ImageField
        gif_bytes = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        archivo_imagen = SimpleUploadedFile('recibo.gif', gif_bytes, content_type='image/gif')

        payload = {
            'reserva': self.reserva.id,
            'referencia': 'TRANS-998877',
            'banco_origen': 'Bancolombia',
            'metodo_pago': 'Transferencia Bancaria',
            'imagen_comprobante': archivo_imagen,
            'descripcion': 'Pago enviado',
            # Parámetros manipulados en navegador:
            'monto': '10.00',
            'estado_transaccion': 'aprobado'
        }

        response = self.client.post(reverse('enviar_comprobante'), data=payload)
        self.assertEqual(response.status_code, 302)

        pago = Pago.objects.get(referencia='TRANS-998877')
        # El monto debe ser 350000.00 (de la reserva), no 10.00
        self.assertEqual(pago.monto, Decimal('350000.00'))
        # El estado debe ser 'pendiente', no 'aprobado'
        self.assertEqual(pago.estado_transaccion, 'pendiente')

    def test_comprobante_disallowed_file_extension(self):
        """
        Verifica que no se permita subir archivos maliciosos (.sh, .exe, .html)
        como comprobantes de pago.
        """
        archivo_malicioso = SimpleUploadedFile('script.sh', b'#!/bin/bash\necho hack', content_type='application/x-sh')
        form = ComprobantePagoForm(
            data={
                'referencia': 'REF-12345',
                'banco_origen': 'Nequi',
                'metodo_pago': 'Transferencia Bancaria'
            },
            files={'imagen_comprobante': archivo_malicioso}
        )
        self.assertFalse(form.is_valid())
        self.assertIn('imagen_comprobante', form.errors)

    def test_iniciar_sesion_form_validation(self):
        """
        Verifica que el formulario de inicio de sesión valide longitudes y rechace datos vacíos.
        """
        form = IniciarSesionForm(data={'username': '', 'password': ''})
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
        self.assertIn('password', form.errors)
