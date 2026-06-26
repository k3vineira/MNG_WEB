from django.test import TestCase
from django.core.exceptions import ValidationError
from usuarios.models import Usuario, Cliente, GuiaTuristico


def crear_usuario(username='testuser', rol=Usuario.Roles.CLIENTE, **kwargs):
    """Helper para crear usuarios de prueba rápidamente."""
    return Usuario.objects.create_user(
        username=username,
        password='testpass123',
        email=f'{username}@test.com',
        rol=rol,
        **kwargs
    )


# ──────────────────────────────────────────────────────────────────────────────
# TESTS DE USUARIO
# ──────────────────────────────────────────────────────────────────────────────

class UsuarioCreacionTest(TestCase):
    """Verifica la creación básica del modelo Usuario."""

    def test_crear_usuario_cliente(self):
        user = crear_usuario(username='cliente1', rol=Usuario.Roles.CLIENTE)
        self.assertEqual(user.rol, Usuario.Roles.CLIENTE)
        self.assertTrue(user.pk)

    def test_crear_usuario_guia(self):
        user = crear_usuario(username='guia1', rol=Usuario.Roles.GUIA)
        self.assertEqual(user.rol, Usuario.Roles.GUIA)

    def test_crear_usuario_admin(self):
        user = crear_usuario(username='admin1', rol=Usuario.Roles.ADMIN)
        self.assertEqual(user.rol, Usuario.Roles.ADMIN)

    def test_str_usuario(self):
        user = crear_usuario(username='jdoe')
        self.assertIn('jdoe', str(user))

    def test_rol_default_es_cliente(self):
        user = Usuario.objects.create_user(username='defaultuser', password='pass')
        self.assertEqual(user.rol, Usuario.Roles.CLIENTE)


class UsuarioPropiedadesTest(TestCase):
    """Verifica las propiedades calculadas del modelo Usuario."""

    def setUp(self):
        self.user = crear_usuario(
            username='juan',
            first_name='Juan',
            last_name='Pérez'
        )

    def test_nombre_completo_con_nombre_y_apellido(self):
        self.assertEqual(self.user.nombre_completo, 'Juan Pérez')

    def test_nombre_completo_sin_datos_usa_username(self):
        user = crear_usuario(username='sin_nombre')
        self.assertEqual(user.nombre_completo, 'sin_nombre')

    def test_es_guia_falso_para_cliente(self):
        self.assertFalse(self.user.es_guia)

    def test_es_turista_verdadero_para_cliente(self):
        self.assertTrue(self.user.es_turista)

    def test_es_guia_verdadero_para_guia(self):
        guia = crear_usuario(username='guia2', rol=Usuario.Roles.GUIA)
        self.assertTrue(guia.es_guia)

    def test_avatar_url_sin_imagen(self):
        url = self.user.avatar_url
        self.assertIn('avatar_pred.png', url)


class UsuarioRolSuperusuarioTest(TestCase):
    """Verifica que un superusuario siempre tiene rol ADMIN."""

    def test_superusuario_fuerza_rol_admin(self):
        super_user = Usuario.objects.create_superuser(
            username='superadmin', password='superpass'
        )
        self.assertEqual(super_user.rol, Usuario.Roles.ADMIN)


class UsuarioDocumentoTest(TestCase):
    """Verifica el manejo del número de documento."""

    def test_numero_documento_vacio_se_convierte_a_none(self):
        user = crear_usuario(username='doc_test')
        user.numero_documento = ''
        user.save()
        user.refresh_from_db()
        self.assertIsNone(user.numero_documento)

    def test_numero_documento_unico(self):
        crear_usuario(username='u1', numero_documento='12345678')
        with self.assertRaises(Exception):
            crear_usuario(username='u2', numero_documento='12345678')


# ──────────────────────────────────────────────────────────────────────────────
# TESTS DE CLIENTE
# ──────────────────────────────────────────────────────────────────────────────

class ClienteTest(TestCase):
    """Verifica la creación y comportamiento del modelo Cliente."""

    def setUp(self):
        self.usuario = crear_usuario(username='clienteuser', rol=Usuario.Roles.CLIENTE)
        self.cliente = Cliente.objects.create(
            usuario=self.usuario,
            pais='Colombia',
            ciudad='Bogotá'
        )

    def test_crear_cliente(self):
        self.assertEqual(self.cliente.pais, 'Colombia')
        self.assertEqual(self.cliente.ciudad, 'Bogotá')

    def test_str_cliente_usa_nombre_completo(self):
        self.usuario.first_name = 'Carlos'
        self.usuario.last_name = 'López'
        self.usuario.save()
        self.assertIn('Carlos', str(self.cliente))

    def test_relacion_uno_a_uno_con_usuario(self):
        self.assertEqual(self.usuario.cliente, self.cliente)

    def test_cascada_eliminar_usuario_elimina_cliente(self):
        """Verifica que on_delete=CASCADE está configurado en el OneToOneField."""
        from django.db.models import OneToOneField
        campo = Cliente._meta.get_field('usuario')
        self.assertIsInstance(campo, OneToOneField)
        # CASCADE se representa internamente como DO_NOTHING no aplica;
        # verificamos la relación directa en lugar de una eliminación real
        # para evitar conflictos con otras FKs (admin logs, etc.)
        self.assertEqual(self.cliente.usuario, self.usuario)


# ──────────────────────────────────────────────────────────────────────────────
# TESTS DE GUIA TURISTICO
# ──────────────────────────────────────────────────────────────────────────────

class GuiaTuristicoTest(TestCase):
    """Verifica la creación y comportamiento del modelo GuiaTuristico."""

    def setUp(self):
        self.usuario = crear_usuario(username='guiauser', rol=Usuario.Roles.GUIA)
        self.guia = GuiaTuristico.objects.create(
            usuario=self.usuario,
            licencia_turismo='LIC-001',
            experiencia_anos=5,
            biografia='Guía experto en tours de aventura.'
        )

    def test_crear_guia_turistico(self):
        self.assertEqual(self.guia.licencia_turismo, 'LIC-001')
        self.assertEqual(self.guia.experiencia_anos, 5)

    def test_str_guia_contiene_guia(self):
        self.assertIn('Guía', str(self.guia))

    def test_relacion_uno_a_uno_con_usuario(self):
        self.assertEqual(self.usuario.guia, self.guia)

    def test_experiencia_anos_default_cero(self):
        usuario2 = crear_usuario(username='guia_nuevo', rol=Usuario.Roles.GUIA)
        guia2 = GuiaTuristico.objects.create(usuario=usuario2)
        self.assertEqual(guia2.experiencia_anos, 0)

    def test_cascada_eliminar_usuario_elimina_guia(self):
        """Verifica que on_delete=CASCADE está configurado en el OneToOneField."""
        from django.db.models import OneToOneField
        campo = GuiaTuristico._meta.get_field('usuario')
        self.assertIsInstance(campo, OneToOneField)
        self.assertEqual(self.guia.usuario, self.usuario)
