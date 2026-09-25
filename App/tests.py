from datetime import date, timedelta
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


class CancelacionReservaTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.turista = Usuario.objects.create_user(
            username='turista_cancelacion',
            email='cancelacion@monagua.com',
            password='Password123#',
            first_name='Ana',
            last_name='Lopez',
            rol=Usuario.Roles.CLIENTE,
            is_staff=False,
            is_superuser=False
        )
        self.categoria = Categoria.objects.create(nombre='Aventura')
        self.paquete = Paquete.objects.create(
            nombre='Tour de prueba',
            descripcion='Aventura de prueba',
            categoria=self.categoria,
            punto_encuentro='Plaza central',
            hora_encuentro='08:00:00',
            dias_duracion=1,
            noches_duracion=1,
            imagen=SimpleUploadedFile('test.jpg', b'contenido_imagen', content_type='image/jpeg')
        )

    def test_reserva_sin_pago_se_descarta_en_lugar_de_cancelarse(self):
        """Si la reserva no tiene pago, se descarta con motivo y queda registrada como cancelación aprobada."""
        self.reserva = Reserva.objects.create(
            usuario=self.turista,
            paquete=self.paquete,
            monto_total=Decimal('350000.00'),
            numero_adultos=2,
            numero_menores=0,
            estado_reserva='pendiente',
            fecha_inicio=date.today() + timedelta(days=10),
            estado_cancelacion='pendiente'
        )
        self.client.force_login(self.turista)

        response = self.client.post(
            reverse('cancelar_reserva_usuario', args=[self.reserva.id]),
            {'motivo_cancelacion': 'Ya no puedo viajar'}
        )

        self.assertEqual(response.status_code, 302)
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.estado_reserva, 'cancelada')
        self.assertEqual(self.reserva.estado_cancelacion, 'aprobada')
        self.assertEqual(self.reserva.motivo_cancelacion, 'Ya no puedo viajar')
        self.assertEqual(self.reserva.penalidad, Decimal('0.00'))

    def test_reserva_no_se_puede_cancelar_si_falta_menos_de_2_dias(self):
        """La cancelación queda bloqueada cuando faltan menos de 2 días para el viaje."""
        self.reserva = Reserva.objects.create(
            usuario=self.turista,
            paquete=self.paquete,
            monto_total=Decimal('350000.00'),
            numero_adultos=2,
            numero_menores=0,
            estado_reserva='pendiente',
            fecha_inicio=date.today() + timedelta(days=1),
            estado_cancelacion='pendiente'
        )
        self.client.force_login(self.turista)

        self.reserva.monto_total = Decimal('350000.00')
        self.reserva.save(update_fields=['monto_total'])

        Pago.objects.create(
            reserva=self.reserva,
            referencia='REF-123',
            banco_origen='Bancolombia',
            metodo_pago='Transferencia Bancaria',
            monto=Decimal('350000.00'),
            imagen_comprobante=SimpleUploadedFile('pago.gif', b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;', content_type='image/gif'),
            descripcion='Pago validado',
            estado_transaccion='aprobado'
        )

        response = self.client.post(
            reverse('cancelar_reserva_usuario', args=[self.reserva.id]),
            {'motivo_cancelacion': 'Se me complicó la fecha'}
        )

        self.assertEqual(response.status_code, 302)
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.estado_cancelacion, 'pendiente')
        self.assertEqual(self.reserva.estado_reserva, 'confirmada')

    def test_reserva_con_cancelacion_pendiente_sigue_apareciendo_en_mis_reservas(self):
        """Una reserva activa no debe desaparecer de la lista de reservas solo por tener una solicitud de cancelación pendiente."""
        self.reserva = Reserva.objects.create(
            usuario=self.turista,
            paquete=self.paquete,
            monto_total=Decimal('350000.00'),
            numero_adultos=2,
            numero_menores=0,
            estado_reserva='confirmada',
            fecha_inicio=date.today() + timedelta(days=10),
            estado_cancelacion='pendiente'
        )
        Pago.objects.create(
            reserva=self.reserva,
            referencia='REF-REQUEST-001',
            banco_origen='Bancolombia',
            metodo_pago='Transferencia Bancaria',
            monto=Decimal('350000.00'),
            imagen_comprobante=SimpleUploadedFile('pago.gif', b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;', content_type='image/gif'),
            descripcion='Pago validado',
            estado_transaccion='aprobado'
        )
        self.client.force_login(self.turista)

        response = self.client.get(reverse('mis_reservas_usuario'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tour de prueba')
        self.assertContains(response, 'Cancelación en revisión')

    def test_mis_reservas_excluye_las_canceladas_y_aprobadas(self):
        """Solo deben salir de Mis Reservas las reservas ya canceladas o aprobadas; las pendientes siguen visibles."""
        activa = Reserva.objects.create(
            usuario=self.turista,
            paquete=self.paquete,
            monto_total=Decimal('350000.00'),
            numero_adultos=2,
            numero_menores=0,
            estado_reserva='confirmada',
            fecha_inicio=date.today() + timedelta(days=30)
        )
        pendiente = Reserva.objects.create(
            usuario=self.turista,
            paquete=self.paquete,
            monto_total=Decimal('350000.00'),
            numero_adultos=2,
            numero_menores=0,
            estado_reserva='confirmada',
            fecha_inicio=date.today() + timedelta(days=15),
            estado_cancelacion='pendiente',
            motivo_cancelacion='Solicituda de cancelación'
        )
        cancelada = Reserva.objects.create(
            usuario=self.turista,
            paquete=self.paquete,
            monto_total=Decimal('350000.00'),
            numero_adultos=2,
            numero_menores=0,
            estado_reserva='cancelada',
            fecha_inicio=date.today() + timedelta(days=10),
            estado_cancelacion='aprobada',
            motivo_cancelacion='Sin pago'
        )
        aprobada_sin_cancelar = Reserva.objects.create(
            usuario=self.turista,
            paquete=self.paquete,
            monto_total=Decimal('350000.00'),
            numero_adultos=2,
            numero_menores=0,
            estado_reserva='confirmada',
            fecha_inicio=date.today() + timedelta(days=20),
            estado_cancelacion='aprobada',
            motivo_cancelacion='Se descartó por falta de pago'
        )

        self.client.force_login(self.turista)
        response = self.client.get(reverse('mis_reservas_usuario'))

        self.assertEqual(response.status_code, 200)
        reservas = list(response.context['reservas'])
        self.assertIn(activa, reservas)
        self.assertIn(pendiente, reservas)
        self.assertNotIn(cancelada, reservas)
        self.assertNotIn(aprobada_sin_cancelar, reservas)

    def test_reserva_cancelada_pero_pendiente_se_normaliza_y_no_aparece_en_mis_reservas(self):
        """Una reserva ya cancelada no debe seguir apareciendo como pendiente ni en la lista activa."""
        reserva = Reserva.objects.create(
            usuario=self.turista,
            paquete=self.paquete,
            monto_total=Decimal('350000.00'),
            numero_adultos=2,
            numero_menores=0,
            estado_reserva='cancelada',
            fecha_inicio=date.today() + timedelta(days=10),
            estado_cancelacion='pendiente',
            motivo_cancelacion='Se registró con estado inconsistente'
        )

        self.client.force_login(self.turista)
        response = self.client.get(reverse('mis_reservas_usuario'))

        reserva.refresh_from_db()
        self.assertEqual(reserva.estado_cancelacion, 'aprobada')
        self.assertEqual(response.status_code, 200)
        self.assertNotIn(reserva, list(response.context['reservas']))

    def test_mis_cancelaciones_muestra_solo_pendientes_o_aprobadas(self):
        """Solo deben aparecer en el historial de cancelaciones las solicitudes pendientes o aprobadas."""
        aprobada = Reserva.objects.create(
            usuario=self.turista,
            paquete=self.paquete,
            monto_total=Decimal('350000.00'),
            numero_adultos=2,
            numero_menores=0,
            estado_reserva='cancelada',
            fecha_inicio=date.today() + timedelta(days=10),
            estado_cancelacion='aprobada',
            motivo_cancelacion='Sin pago'
        )
        pendiente = Reserva.objects.create(
            usuario=self.turista,
            paquete=self.paquete,
            monto_total=Decimal('350000.00'),
            numero_adultos=2,
            numero_menores=0,
            estado_reserva='confirmada',
            fecha_inicio=date.today() + timedelta(days=15),
            estado_cancelacion='pendiente',
            motivo_cancelacion='Solicituda de cancelación'
        )
        rechazada = Reserva.objects.create(
            usuario=self.turista,
            paquete=self.paquete,
            monto_total=Decimal('350000.00'),
            numero_adultos=2,
            numero_menores=0,
            estado_reserva='confirmada',
            fecha_inicio=date.today() + timedelta(days=20),
            estado_cancelacion='rechazada',
            motivo_cancelacion='No procede'
        )

        self.client.force_login(self.turista)
        response = self.client.get(reverse('mis_cancelaciones'))

        self.assertEqual(response.status_code, 200)
        cancelaciones = list(response.context['cancelaciones'])
        self.assertIn(aprobada, cancelaciones)
        self.assertIn(pendiente, cancelaciones)
        self.assertNotIn(rechazada, cancelaciones)
