from django.test import TestCase
from usuarios.models import Usuario, Cliente
from catalogo.models import Categoria, Paquete
from comunidad.models import Calificacion, Blog, PQRS, Comentario
import datetime


def crear_usuario(username='testuser', rol=Usuario.Roles.CLIENTE):
    """
    crear_usuario.
    
    :param username='testuser': Descripción del parámetro.
    
    :param rol=Usuario.Roles.CLIENTE: Descripción del parámetro.
    
    :return: Respuesta de la función.
    """
    return Usuario.objects.create_user(
        username=username,
        password='pass123',
        email=f'{username}@test.com',
        rol=rol
    )


def crear_cliente(username='cliente_test'):
    """
    crear_cliente.
    
    :param username='cliente_test': Descripción del parámetro.
    
    :return: Respuesta de la función.
    """
    usuario = crear_usuario(username=username)
    return Cliente.objects.create(usuario=usuario)


def crear_paquete():
    """
    crear_paquete.
    
    :return: Respuesta de la función.
    """
    cat = Categoria.objects.create(nombre='Test Cat', descripcion='Desc')
    return Paquete.objects.create(
        nombre='Paquete Test',
        descripcion='Desc',
        dias_duracion=1,
        noches_duracion=0,
        punto_encuentro='Plaza',
        hora_encuentro=datetime.time(8, 0),
        categoria=cat
    )


# ──────────────────────────────────────────────────────────────────────────────
# TESTS DE CALIFICACION
# ──────────────────────────────────────────────────────────────────────────────

class CalificacionTest(TestCase):

    def setUp(self):
        """
        setUp.
        
        :return: Respuesta de la función.
        """
        self.cliente = crear_cliente()
        self.paquete = crear_paquete()

    def test_crear_calificacion(self):
        """
        test_crear_calificacion.
        
        :return: Respuesta de la función.
        """
        cal = Calificacion.objects.create(
            cliente=self.cliente,
            paquete=self.paquete,
            puntaje=5,
            comentario='Excelente tour'
        )
        self.assertEqual(cal.puntaje, 5)
        self.assertEqual(cal.comentario, 'Excelente tour')

    def test_unique_together_cliente_paquete(self):
        """
        test_unique_together_cliente_paquete.
        
        :return: Respuesta de la función.
        """
        Calificacion.objects.create(
            cliente=self.cliente,
            paquete=self.paquete,
            puntaje=4
        )
        with self.assertRaises(Exception):
            Calificacion.objects.create(
                cliente=self.cliente,
                paquete=self.paquete,
                puntaje=3
            )

    def test_comentario_puede_estar_vacio(self):
        """
        test_comentario_puede_estar_vacio.
        
        :return: Respuesta de la función.
        """
        cal = Calificacion.objects.create(
            cliente=self.cliente,
            paquete=self.paquete,
            puntaje=3,
            comentario=''
        )
        self.assertEqual(cal.comentario, '')


# ──────────────────────────────────────────────────────────────────────────────
# TESTS DE BLOG
# ──────────────────────────────────────────────────────────────────────────────

class BlogTest(TestCase):

    def test_crear_blog(self):
        """
        test_crear_blog.
        
        :return: Respuesta de la función.
        """
        blog = Blog.objects.create(
            titulo='Guía de Monagua',
            contenido='Contenido del artículo de prueba',
            publicado=True
        )
        self.assertEqual(blog.titulo, 'Guía de Monagua')
        self.assertTrue(blog.publicado)

    def test_str_blog(self):
        """
        test_str_blog.
        
        :return: Respuesta de la función.
        """
        blog = Blog.objects.create(
            titulo='Primer Post',
            contenido='Texto de prueba'
        )
        self.assertEqual(str(blog), 'Primer Post')

    def test_publicado_default_true(self):
        """
        test_publicado_default_true.
        
        :return: Respuesta de la función.
        """
        blog = Blog.objects.create(titulo='Post', contenido='Texto')
        self.assertTrue(blog.publicado)

    def test_get_absolute_url(self):
        """
        test_get_absolute_url.
        
        :return: Respuesta de la función.
        """
        blog = Blog.objects.create(titulo='URL Test', contenido='Texto')
        url = blog.get_absolute_url()
        self.assertIn(str(blog.pk), url)

    def test_ordenamiento_por_fecha_descendente(self):
        """
        test_ordenamiento_por_fecha_descendente.
        
        :return: Respuesta de la función.
        """
        b1 = Blog.objects.create(titulo='Primero', contenido='a')
        b2 = Blog.objects.create(titulo='Segundo', contenido='b')
        blogs = list(Blog.objects.all())
        # El más reciente (b2) debe aparecer primero
        self.assertEqual(blogs[0].pk, b2.pk)


# ──────────────────────────────────────────────────────────────────────────────
# TESTS DE PQRS
# ──────────────────────────────────────────────────────────────────────────────

class PQRSTest(TestCase):

    def setUp(self):
        """
        setUp.
        
        :return: Respuesta de la función.
        """
        self.cliente = crear_cliente(username='pqrs_user')

    def test_crear_pqrs(self):
        """
        test_crear_pqrs.
        
        :return: Respuesta de la función.
        """
        pqrs = PQRS.objects.create(
            cliente=self.cliente,
            tipo='queja',
            asunto='Problema con la reserva',
            descripcion='Descripción detallada del problema'
        )
        self.assertEqual(pqrs.tipo, 'queja')
        self.assertEqual(pqrs.estado, 'abierto')

    def test_estado_default_abierto(self):
        """
        test_estado_default_abierto.
        
        :return: Respuesta de la función.
        """
        pqrs = PQRS.objects.create(
            tipo='sugerencia',
            asunto='Sugerencia',
            descripcion='Texto'
        )
        self.assertEqual(pqrs.estado, 'abierto')

    def test_pqrs_sin_cliente(self):
        """
        test_pqrs_sin_cliente.
        
        :return: Respuesta de la función.
        """
        pqrs = PQRS.objects.create(
            cliente=None,
            tipo='peticion',
            asunto='Asunto anonimo',
            descripcion='Texto anonimo'
        )
        self.assertIsNone(pqrs.cliente)

    def test_choices_tipo_validos(self):
        """
        test_choices_tipo_validos.
        
        :return: Respuesta de la función.
        """
        tipos = [t[0] for t in PQRS.TIPO_CHOICES]
        for tipo in ['peticion', 'queja', 'reclamo', 'sugerencia']:
            self.assertIn(tipo, tipos)

    def test_choices_estado_validos(self):
        """
        test_choices_estado_validos.
        
        :return: Respuesta de la función.
        """
        estados = [e[0] for e in PQRS.ESTADO_CHOICES]
        for estado in ['abierto', 'en_proceso', 'cerrado']:
            self.assertIn(estado, estados)


# ──────────────────────────────────────────────────────────────────────────────
# TESTS DE COMENTARIO
# ──────────────────────────────────────────────────────────────────────────────

class ComentarioTest(TestCase):

    def setUp(self):
        """
        setUp.
        
        :return: Respuesta de la función.
        """
        self.usuario = crear_usuario(username='comentador')
        self.paquete = crear_paquete()

    def test_crear_comentario_con_paquete(self):
        """
        test_crear_comentario_con_paquete.
        
        :return: Respuesta de la función.
        """
        com = Comentario.objects.create(
            usuario=self.usuario,
            tipo='experiencia',
            titulo='Increíble',
            mensaje='Fue una experiencia maravillosa.',
            valoracion=5,
            paquete=self.paquete
        )
        self.assertEqual(com.valoracion, 5)
        self.assertTrue(com.visible)

    def test_crear_comentario_sin_paquete(self):
        """
        test_crear_comentario_sin_paquete.
        
        :return: Respuesta de la función.
        """
        com = Comentario.objects.create(
            usuario=self.usuario,
            mensaje='Comentario general'
        )
        self.assertIsNone(com.paquete)

    def test_str_comentario(self):
        """
        test_str_comentario.
        
        :return: Respuesta de la función.
        """
        com = Comentario.objects.create(
            usuario=self.usuario,
            titulo='Mi título',
            mensaje='Texto'
        )
        self.assertIn(self.usuario.username, str(com))
        self.assertIn('Mi título', str(com))

    def test_str_comentario_sin_titulo(self):
        """
        test_str_comentario_sin_titulo.
        
        :return: Respuesta de la función.
        """
        com = Comentario.objects.create(
            usuario=self.usuario,
            mensaje='Sin título'
        )
        self.assertIn('sin título', str(com))

    def test_visible_default_true(self):
        """
        test_visible_default_true.
        
        :return: Respuesta de la función.
        """
        com = Comentario.objects.create(
            usuario=self.usuario,
            mensaje='Visible'
        )
        self.assertTrue(com.visible)

    def test_valoracion_default_cinco(self):
        """
        test_valoracion_default_cinco.
        
        :return: Respuesta de la función.
        """
        com = Comentario.objects.create(
            usuario=self.usuario,
            mensaje='Con valoración default'
        )
        self.assertEqual(com.valoracion, 5)

    def test_ordenamiento_descendente_por_fecha(self):
        """
        test_ordenamiento_descendente_por_fecha.
        
        :return: Respuesta de la función.
        """
        c1 = Comentario.objects.create(usuario=self.usuario, mensaje='Primero')
        c2 = Comentario.objects.create(usuario=self.usuario, mensaje='Segundo')
        comentarios = list(Comentario.objects.all())
        self.assertEqual(comentarios[0].pk, c2.pk)
