from django.test import TestCase
from django.core import mail
from datetime import time
from core.utils import plantilla_reserva_html, plantilla_cancelacion_html, enviar_correo_html_monagua

class CoreUtilsTestCase(TestCase):
    def test_plantilla_reserva_html_confirmada(self):
        """
        test_plantilla_reserva_html_confirmada.
        
        :return: Respuesta de la función.
        """
        html = plantilla_reserva_html(
            nombre_cliente='Juan Pérez',
            paquete='Laguna de Tota',
            fecha='2026-07-15',
            adultos=2,
            menores=1,
            punto_encuentro='Plaza Principal',
            hora_encuentro='08:30',
            estado='confirmada',
            reserva_id='100',
            monto_total='250000'
        )
        self.assertIn('Juan Pérez', html)
        self.assertIn('Laguna de Tota', html)
        self.assertIn('Reserva Confirmada', html)
        self.assertIn('08:30', html)
        self.assertIn('2 Adultos', html)
        self.assertIn('1 Menores', html)

    def test_plantilla_reserva_html_time_parsing(self):
        """
        test_plantilla_reserva_html_time_parsing.
        
        :return: Respuesta de la función.
        """
        # Test default fallback when time string is invalid
        html = plantilla_reserva_html(
            nombre_cliente='Juan Pérez',
            paquete='Laguna de Tota',
            fecha='2026-07-15',
            punto_encuentro='Plaza Principal',
            hora_encuentro='invalid_time',
            estado='pendiente'
        )
        self.assertIn('00:00', html)

    def test_plantilla_cancelacion_html_aceptada(self):
        """
        test_plantilla_cancelacion_html_aceptada.
        
        :return: Respuesta de la función.
        """
        html = plantilla_cancelacion_html(
            nombre_cliente='Juan Pérez',
            paquete='Laguna de Tota',
            estado='aceptada',
            penalidad='50000'
        )
        self.assertIn('Juan Pérez', html)
        self.assertIn('Laguna de Tota', html)
        self.assertIn('50000', html)
        self.assertIn('Solicitud Aceptada', html)

    def test_enviar_correo_html_monagua(self):
        """
        test_enviar_correo_html_monagua.
        
        :return: Respuesta de la función.
        """
        enviar_correo_html_monagua(
            asunto='Prueba de Correo',
            mensaje_texto='Hola Mundo',
            destinatario='dest@example.com',
            html_contenido='<h1>Hola</h1>'
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].subject, 'Prueba de Correo')
        self.assertEqual(mail.outbox[0].to, ['dest@example.com'])
        self.assertEqual(mail.outbox[0].body, 'Hola Mundo')
