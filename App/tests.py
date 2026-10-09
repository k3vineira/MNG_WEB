import re
from datetime import date, timedelta
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.core import mail
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

    def test_pago_penalidad_esta_disponible_en_enviar_comprobante(self):
        """Una cancelación aprobada con penalidad debe aparecer como opción de pago en la vista de comprobantes."""
        reserva_penalidad = Reserva.objects.create(
            usuario=self.turista,
            paquete=self.paquete,
            monto_total=Decimal('350000.00'),
            numero_adultos=2,
            numero_menores=0,
            estado_reserva='cancelada',
            estado_cancelacion='aprobada',
            penalidad=Decimal('15000.00'),
            fecha_inicio=date.today() + timedelta(days=10),
            motivo_cancelacion='Cambio de planes'
        )
        self.client.force_login(self.turista)

        response = self.client.get(reverse('enviar_comprobante'), {'reserva_id': reserva_penalidad.id})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '[Multa]')
        self.assertContains(response, 'Valor:')
        self.assertContains(response, 'Monto de la Penalidad')

        gif_bytes = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
        payload = {
            'reserva': reserva_penalidad.id,
            'referencia': 'PENALIDAD-123',
            'banco_origen': 'Daviplata',
            'metodo_pago': 'Transferencia Bancaria',
            'imagen_comprobante': SimpleUploadedFile('penalidad.gif', gif_bytes, content_type='image/gif'),
            'descripcion': 'Pago de penalidad'
        }

        response = self.client.post(reverse('enviar_comprobante'), data=payload)
        self.assertEqual(response.status_code, 302)
        pago = Pago.objects.get(reserva=reserva_penalidad)
        self.assertEqual(pago.monto, Decimal('15000.00'))
        self.assertEqual(pago.estado_transaccion, 'pendiente')

        comprobantes = self.client.get(reverse('mis_comprobantes'))
        self.assertEqual(comprobantes.status_code, 200)
        self.assertContains(comprobantes, 'Penalidad')
        self.assertContains(comprobantes, 'Reserva')

    def test_pago_penalidad_en_url_directa_usa_tipo_penalidad(self):
        """Una URL directa con tipo=penalidad debe mostrar inmediatamente el formulario de penalidad, aunque la reserva aún esté en flujo de revisión."""
        reserva_penalidad = Reserva.objects.create(
            usuario=self.turista,
            paquete=self.paquete,
            monto_total=Decimal('350000.00'),
            numero_adultos=2,
            numero_menores=0,
            estado_reserva='pendiente',
            estado_cancelacion='pendiente',
            penalidad=Decimal('15000.00'),
            fecha_inicio=date.today() + timedelta(days=10),
            motivo_cancelacion='Cambio de planes'
        )
        self.client.force_login(self.turista)

        response = self.client.get(reverse('enviar_comprobante'), {'reserva_id': reserva_penalidad.id, 'tipo': 'penalidad'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Penalidad a Vincular')
        self.assertEqual(response.context['selected_tipo'], 'penalidad')

    def test_pago_penalidad_directa_sigue_mostrando_la_opcion_si_ya_hay_pago_pendiente(self):
        """Si un usuario llega por URL directa a una penalidad con pago pendiente, el select debe seguir mostrando esa penalidad y no el placeholder."""
        reserva_penalidad = Reserva.objects.create(
            usuario=self.turista,
            paquete=self.paquete,
            monto_total=Decimal('350000.00'),
            numero_adultos=2,
            numero_menores=0,
            estado_reserva='cancelada',
            estado_cancelacion='aprobada',
            penalidad=Decimal('15000.00'),
            fecha_inicio=date.today() + timedelta(days=14),
            motivo_cancelacion='Cambio de planes pendiente'
        )
        Pago.objects.create(
            reserva=reserva_penalidad,
            referencia='PEN-EXISTENTE',
            banco_origen='Daviplata',
            monto=Decimal('15000.00'),
            estado_transaccion='pendiente',
            imagen_comprobante=SimpleUploadedFile('penalidad_existente.gif', b'GIF89a', content_type='image/gif')
        )
        self.client.force_login(self.turista)

        response = self.client.get(reverse('enviar_comprobante'), {'reserva_id': reserva_penalidad.id, 'tipo': 'penalidad'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Penalidad a Vincular')
        self.assertContains(response, str(reserva_penalidad.id))
        self.assertNotContains(response, 'Selecciona laaaaaaaaaa reserva')

    def test_pago_penalidad_multiple_elige_una_opcion_unica(self):
        """Cuando hay varias penalidades, la vista debe elegir una sola opción y no dejar el select en el placeholder."""
        reserva1 = Reserva.objects.create(
            usuario=self.turista,
            paquete=self.paquete,
            monto_total=Decimal('350000.00'),
            numero_adultos=2,
            numero_menores=0,
            estado_reserva='cancelada',
            estado_cancelacion='aprobada',
            penalidad=Decimal('15000.00'),
            fecha_inicio=date.today() + timedelta(days=12),
            motivo_cancelacion='Cambio de planes 1'
        )
        reserva2 = Reserva.objects.create(
            usuario=self.turista,
            paquete=self.paquete,
            monto_total=Decimal('450000.00'),
            numero_adultos=2,
            numero_menores=0,
            estado_reserva='cancelada',
            estado_cancelacion='aprobada',
            penalidad=Decimal('20000.00'),
            fecha_inicio=date.today() + timedelta(days=20),
            motivo_cancelacion='Cambio de planes 2'
        )
        self.client.force_login(self.turista)

        response = self.client.get(reverse('enviar_comprobante'), {'tipo': 'penalidad'})
        html = response.content.decode()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['selected_tipo'], 'penalidad')
        self.assertIn(str(reserva1.id), html)
        self.assertEqual(len(re.findall(r'data-tipo="penalidad"[^>]*selected', html)), 1)

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

    def test_reserva_con_pago_queda_cancelada_al_solicitar_cancelacion(self):
        """Cuando el usuario solicita cancelar una reserva pagada, el estado principal debe pasar a cancelada."""
        self.reserva = Reserva.objects.create(
            usuario=self.turista,
            paquete=self.paquete,
            numero_adultos=2,
            numero_menores=0,
            estado_reserva='confirmada',
            fecha_inicio=date.today() + timedelta(days=10),
            estado_cancelacion=None
        )
        self.reserva.monto_total = Decimal('350000.00')
        self.reserva.save(update_fields=['monto_total'])
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

        response = self.client.post(
            reverse('cancelar_reserva_usuario', args=[self.reserva.id]),
            {'motivo_cancelacion': 'Necesito cancelar la reserva'}
        )

        self.assertEqual(response.status_code, 302)
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.estado_reserva, 'cancelada')
        self.assertEqual(self.reserva.estado_cancelacion, 'pendiente')

    def test_reserva_con_pago_y_sin_penalidad_se_aprueba_automaticamente(self):
        """Si la cancelación no genera multa, debe aprobarse automáticamente y no quedar en revisión."""
        self.reserva = Reserva.objects.create(
            usuario=self.turista,
            paquete=self.paquete,
            numero_adultos=2,
            numero_menores=0,
            estado_reserva='confirmada',
            fecha_inicio=None,
            estado_cancelacion=None
        )
        self.reserva.monto_total = Decimal('350000.00')
        self.reserva.save(update_fields=['monto_total'])
        Pago.objects.create(
            reserva=self.reserva,
            referencia='REF-APPROVE-AUTO',
            banco_origen='Daviplata',
            metodo_pago='Transferencia Bancaria',
            monto=Decimal('350000.00'),
            imagen_comprobante=SimpleUploadedFile('pago.gif', b'GIF89a\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;', content_type='image/gif'),
            descripcion='Pago validado',
            estado_transaccion='aprobado'
        )
        self.client.force_login(self.turista)

        response = self.client.post(
            reverse('cancelar_reserva_usuario', args=[self.reserva.id]),
            {'motivo_cancelacion': 'Cambio de planes'}
        )

        self.assertEqual(response.status_code, 302)
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.estado_reserva, 'cancelada')
        self.assertEqual(self.reserva.estado_cancelacion, 'aprobada')

    def test_mis_cancelaciones_muestra_boton_pagar_cuando_hay_penalidad_aprobada(self):
        """Si la cancelación fue aprobada con penalidad, el usuario debe poder pagar la penalidad desde la página de cancelaciones."""
        reserva = Reserva.objects.create(
            usuario=self.turista,
            paquete=self.paquete,
            monto_total=Decimal('350000.00'),
            numero_adultos=2,
            numero_menores=0,
            estado_reserva='cancelada',
            fecha_inicio=date.today() + timedelta(days=10),
            estado_cancelacion='aprobada',
            motivo_cancelacion='Solicituda de cancelación',
            penalidad=Decimal('15000.00')
        )
        self.client.force_login(self.turista)

        response = self.client.get(reverse('mis_cancelaciones'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pagar penalidad')
        self.assertContains(response, 'Penalidad:')

    def test_mis_cancelaciones_muestra_boton_pagar_penalidad_solo_cuando_hay_penalidad(self):
        """La acción de pago debe ser por penalidad y no aparecer cuando no hay multa."""
        Reserva.objects.create(
            usuario=self.turista,
            paquete=self.paquete,
            monto_total=Decimal('350000.00'),
            numero_adultos=2,
            numero_menores=0,
            estado_reserva='cancelada',
            fecha_inicio=date.today() + timedelta(days=10),
            estado_cancelacion='aprobada',
            motivo_cancelacion='Solicituda de cancelación',
            penalidad=Decimal('15000.00')
        )
        Reserva.objects.create(
            usuario=self.turista,
            paquete=self.paquete,
            monto_total=Decimal('350000.00'),
            numero_adultos=2,
            numero_menores=0,
            estado_reserva='cancelada',
            fecha_inicio=date.today() + timedelta(days=12),
            estado_cancelacion='aprobada',
            motivo_cancelacion='Cancelación sin multa',
            penalidad=Decimal('0.00')
        )
        self.client.force_login(self.turista)

        response = self.client.get(reverse('mis_cancelaciones'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Pagar penalidad')
        self.assertContains(response, 'Sin multa')
        self.assertNotContains(response, 'Pagar reserva')

    def test_mis_reservas_excluye_las_canceladas_y_solicitudes_de_cancelacion(self):
        """Si la reserva fue cancelada por el usuario, ya no debe seguir visible en Mis Reservas."""
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
        self.assertNotIn(pendiente, reservas)
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

    def test_reserva_aprobada_pero_activa_se_normaliza_a_cancelada(self):
        """Si la cancelación ya fue aprobada, la reserva debe quedar en estado cancelado aunque el dato esté inconsistente."""
        reserva = Reserva.objects.create(
            usuario=self.turista,
            paquete=self.paquete,
            monto_total=Decimal('350000.00'),
            numero_adultos=2,
            numero_menores=0,
            estado_reserva='confirmada',
            fecha_inicio=date.today() + timedelta(days=15),
            estado_cancelacion='aprobada',
            motivo_cancelacion='Se marcó con aprobación pero quedó activa'
        )

        self.client.force_login(self.turista)
        response = self.client.get(reverse('mis_reservas_usuario'))

        reserva.refresh_from_db()
        self.assertEqual(reserva.estado_reserva, 'cancelada')
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


class EmailReservaYCancelacionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = Usuario.objects.create_user(
            username='admin_email',
            email='admin@monagua.com',
            password='Password123#',
            first_name='Admin',
            last_name='Monagua',
            rol=Usuario.Roles.ADMIN,
            is_staff=True,
            is_superuser=False,
        )
        self.turista = Usuario.objects.create_user(
            username='turista_email_unique',
            email='turista_unique@monagua.com',
            password='Password123#',
            first_name='Andrés',
            last_name='Pérez',
            tipo_documento='CC',
            numero_documento='1234567890',
            telefono='3001234567',
            rol=Usuario.Roles.CLIENTE,
            is_staff=False,
            is_superuser=False,
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

    def test_html_reserva_usa_logo_y_color_monagua(self):
        from App.utils import plantilla_reserva_html

        html = plantilla_reserva_html(
            nombre_cliente='Andrés',
            paquete='Tour de prueba',
            fecha='12/12/2026',
            adultos=2,
            menores=1,
            punto_encuentro='Plaza central',
            hora_encuentro='08:00',
            estado='confirmada',
            reserva_id='99',
            monto_total='350000'
        )

        self.assertIn('#2c6e3c', html)
        self.assertIn('logo_monagua', html)

    def test_admin_approval_of_cancellation_sends_email(self):
        reserva = Reserva.objects.create(
            usuario=self.turista,
            paquete=self.paquete,
            monto_total=Decimal('350000.00'),
            numero_adultos=2,
            numero_menores=0,
            estado_reserva='cancelada',
            fecha_inicio=date.today() + timedelta(days=15),
            estado_cancelacion='pendiente',
            motivo_cancelacion='Cambio de planes',
            penalidad=Decimal('15000.00'),
        )
        self.client.force_login(self.admin)

        with self.settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend'):
            mail.outbox.clear()
            response = self.client.post(
                reverse('editar_cancelacion_admin', args=[reserva.id]),
                {'estado_cancelacion': 'aprobada'}
            )

            self.assertEqual(response.status_code, 302)
            self.assertEqual(len(mail.outbox), 1)
            self.assertIn('Monagua', mail.outbox[0].subject)
            self.assertIn('#2c6e3c', mail.outbox[0].alternatives[0][0])


class CrudBootstrapConsistencyTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin = Usuario.objects.create_user(
            username='admin_bootstrap',
            email='admin@monagua.com',
            password='Password123#',
            first_name='Admin',
            last_name='Bootstrap',
            rol=Usuario.Roles.ADMIN,
            is_staff=True,
            is_superuser=False,
        )
        self.categoria = Categoria.objects.create(nombre='Aventura', estado=True)
        self.paquete = Paquete.objects.create(
            nombre='Ruta de la Cueva',
            descripcion='Recorrido en la montaña',
            categoria=self.categoria,
            punto_encuentro='Plaza central',
            hora_encuentro='08:00:00',
            dias_duracion=2,
            noches_duracion=1,
            estado=True,
            imagen=SimpleUploadedFile('test.jpg', b'contenido_imagen', content_type='image/jpeg'),
        )
        from App.models import Temporada, Actividades, Tarifa

        self.temporada = Temporada.objects.create(
            nombre='Alta Temporada',
            descripcion='Temporada alta',
            fecha_inicio=date.today(),
            fecha_fin=date.today() + timedelta(days=15),
            estado=True,
        )
        self.actividad = Actividades.objects.create(
            nombre='Senderismo',
            descripcion='Senderismo guiado',
            apto_menores=True,
            estado=True,
        )
        self.tarifa = Tarifa.objects.create(
            paquete=self.paquete,
            temporada=self.temporada,
            precio_adulto=150000,
            precio_menor=100000,
            estado=True,
        )

    def test_delete_forms_use_consistent_bootstrap_action_buttons(self):
        self.client.force_login(self.admin)

        urls_to_check = [
            ('eliminar_paquete', self.paquete.id),
            ('eliminar_categoria', self.categoria.id),
            ('eliminar_temporada', self.temporada.id),
            ('eliminar_actividad', self.actividad.id),
            ('eliminar_tarifa', self.tarifa.id),
        ]

        for url_name, obj_id in urls_to_check:
            with self.subTest(url_name=url_name):
                response = self.client.get(reverse(url_name, args=[obj_id]))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'Confirmar Eliminación')
                self.assertContains(response, 'btn btn-danger px-4 rounded-pill fw-bold')
                self.assertContains(response, 'btn btn-outline-secondary px-4 rounded-pill fw-semibold')

    def test_create_and_edit_forms_use_same_green_header(self):
        self.client.force_login(self.admin)

        urls_to_check = [
            ('crear_paquete', None),
            ('editar_paquete', self.paquete.id),
            ('crear_categoria', None),
            ('editar_categoria', self.categoria.id),
            ('crear_temporada', None),
            ('editar_temporada', self.temporada.id),
            ('crear_actividad', None),
            ('editar_actividad', self.actividad.id),
            ('crear_tarifa', None),
            ('editar_tarifa', self.tarifa.id),
        ]

        for url_name, obj_id in urls_to_check:
            with self.subTest(url_name=url_name):
                if obj_id is None:
                    response = self.client.get(reverse(url_name))
                else:
                    response = self.client.get(reverse(url_name, args=[obj_id]))
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'bg-success text-white p-4 border-0')
                self.assertContains(response, 'btn btn-success px-4 rounded-pill shadow-sm fw-bold')
