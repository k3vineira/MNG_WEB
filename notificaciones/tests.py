from django.test import TestCase
from django.contrib.auth import get_user_model
from notificaciones.models import Notificacion
from notificaciones.utils import crear_notificacion_sistema

Usuario = get_user_model()

class NotificacionesTestCase(TestCase):
    def setUp(self):
        """
        setUp.
        
        :return: Respuesta de la función.
        """
        # Crear usuario de prueba
        self.user = Usuario.objects.create_user(
            username='user_notif',
            email='user@notif.com',
            password='password123'
        )

    def test_crear_notificacion_sistema_exito(self):
        """
        test_crear_notificacion_sistema_exito.
        
        :return: Respuesta de la función.
        """
        # Crear notificación utilizando el utilitario
        notificacion = crear_notificacion_sistema(
            usuario=self.user,
            titulo="Nueva Alerta",
            mensaje="Esto es un mensaje de alerta de prueba.",
            tipo="sistema"
        )
        
        self.assertIsNotNone(notificacion)
        self.assertEqual(notificacion.cliente, self.user)
        self.assertEqual(notificacion.titulo, "Nueva Alerta")
        self.assertEqual(notificacion.mensaje, "Esto es un mensaje de alerta de prueba.")
        self.assertEqual(notificacion.tipo, "sistema")
        self.assertFalse(notificacion.leida)  # Por defecto no leída

    def test_crear_notificacion_usuario_no_autenticado(self):
        """
        test_crear_notificacion_usuario_no_autenticado.
        
        :return: Respuesta de la función.
        """
        # Si pasamos un usuario no autenticado (o None), debe retornar None
        notificacion = crear_notificacion_sistema(
            usuario=None,
            titulo="Alerta Anónima",
            mensaje="Prueba anónima.",
            tipo="sistema"
        )
        self.assertIsNone(notificacion)

    def test_marcar_notificacion_como_leida(self):
        """
        test_marcar_notificacion_como_leida.
        
        :return: Respuesta de la función.
        """
        notificacion = Notificacion.objects.create(
            cliente=self.user,
            titulo="Reserva Confirmada",
            mensaje="Tu reserva #123 ha sido confirmada.",
            tipo="reserva"
        )
        
        self.assertFalse(notificacion.leida)
        
        # Simular lectura
        notificacion.leida = True
        notificacion.save()
        
        # Recargar de base de datos
        notificacion.refresh_from_db()
        self.assertTrue(notificacion.leida)
