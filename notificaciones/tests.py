from django.test import TestCase
from django.conf import settings
from usuarios.models import Usuario
from notificaciones.models import Notificacion


def crear_usuario(username='notif_user'):
    return Usuario.objects.create_user(
        username=username,
        password='pass123',
        email=f'{username}@test.com'
    )


# ──────────────────────────────────────────────────────────────────────────────
# TESTS DE NOTIFICACION
# ──────────────────────────────────────────────────────────────────────────────

class NotificacionCreacionTest(TestCase):

    def setUp(self):
        self.usuario = crear_usuario()

    def test_crear_notificacion(self):
        notif = Notificacion.objects.create(
            cliente=self.usuario,
            titulo='Nueva reserva',
            mensaje='Tu reserva fue confirmada',
            tipo='reserva'
        )
        self.assertEqual(notif.titulo, 'Nueva reserva')
        self.assertEqual(notif.tipo, 'reserva')
        self.assertFalse(notif.leida)

    def test_str_notificacion(self):
        notif = Notificacion.objects.create(
            cliente=self.usuario,
            titulo='Alerta del sistema',
            mensaje='Mensaje de prueba',
            tipo='sistema'
        )
        resultado = str(notif)
        self.assertIn('Alerta del sistema', resultado)
        self.assertIn(self.usuario.username, resultado)

    def test_leida_default_false(self):
        notif = Notificacion.objects.create(
            cliente=self.usuario,
            titulo='Sin leer',
            mensaje='Texto'
        )
        self.assertFalse(notif.leida)

    def test_tipo_default_sistema(self):
        notif = Notificacion.objects.create(
            cliente=self.usuario,
            titulo='Default tipo',
            mensaje='Texto'
        )
        self.assertEqual(notif.tipo, 'sistema')

    def test_marcar_como_leida(self):
        notif = Notificacion.objects.create(
            cliente=self.usuario,
            titulo='Para leer',
            mensaje='Texto'
        )
        notif.leida = True
        notif.save()
        notif.refresh_from_db()
        self.assertTrue(notif.leida)

    def test_choices_tipo_validos(self):
        tipos = [t[0] for t in Notificacion.TIPO_CHOICES]
        self.assertIn('reserva', tipos)
        self.assertIn('pqrs', tipos)
        self.assertIn('sistema', tipos)

    def test_ordenamiento_descendente_por_fecha(self):
        n1 = Notificacion.objects.create(
            cliente=self.usuario, titulo='Primera', mensaje='a')
        n2 = Notificacion.objects.create(
            cliente=self.usuario, titulo='Segunda', mensaje='b')
        notifs = list(Notificacion.objects.all())
        self.assertEqual(notifs[0].pk, n2.pk)

    def test_multiples_notificaciones_para_mismo_usuario(self):
        for i in range(3):
            Notificacion.objects.create(
                cliente=self.usuario,
                titulo=f'Notif {i}',
                mensaje=f'Texto {i}'
            )
        self.assertEqual(Notificacion.objects.filter(cliente=self.usuario).count(), 3)

    def test_eliminacion_en_cascada_con_usuario(self):
        Notificacion.objects.create(
            cliente=self.usuario,
            titulo='A eliminar',
            mensaje='Texto'
        )
        pk_usuario = self.usuario.pk
        self.usuario.delete()
        self.assertEqual(Notificacion.objects.filter(cliente_id=pk_usuario).count(), 0)
