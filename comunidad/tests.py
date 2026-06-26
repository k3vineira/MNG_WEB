from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import  Blog, PQRS, Comentario

Usuario = get_user_model()

class MockCliente:
    def __init__(self, id):
        self.id = id
        self.pk = id

class MonaguaInteraccionModelosTest(TestCase):

    def setUp(self):
        self.user_admin = Usuario.objects.create_user(
            username="admin_test",
            email="admin@monagua.com",
            password="password123"
        )
        self.blog = Blog.objects.create(
            titulo="Descubriendo Mongua",
            contenido="Un viaje al Páramo de Ocetá.",
            informacion_adicional="Llevar ropa abrigada.",
            publicado=True
        )
        self.pqrs = PQRS.objects.create(
            tipo="queja",
            asunto="Error en pasarela",
            descripcion="No cargó el botón de pago.",
            estado="abierto"
        )
        self.comentario = Comentario.objects.create(
            usuario=self.user_admin,
            tipo="experiencia",
            titulo="Excelente tour",
            mensaje="Me encantó la guía por el municipio.",
            valoracion=5,
            visible=True
        )

    def test_modelo_blog_str(self):
        self.assertEqual(str(self.blog), "Descubriendo Mongua")

    def test_blog_get_absolute_url(self):
        self.assertEqual(self.blog.get_absolute_url(), f"/detalle_blog/{self.blog.id}")

    def test_modelo_pqrs_valores_por_defecto(self):
        self.assertEqual(self.pqrs.estado, "abierto")

    def test_pqrs_choices_invalidas(self):
        self.pqrs.tipo = "invalido"
        with self.assertRaises(ValidationError):
            self.pqrs.full_clean()

    def test_modelo_comentario_str(self):
        esperado = f"Comentario de {self.user_admin.username} - Excelente tour"
        self.assertEqual(str(self.comentario), esperado)

    def test_comentario_valoracion_por_defecto(self):
        comentario_nuevo = Comentario.objects.create(
            usuario=self.user_admin,
            mensaje="Pregunta corta"
        )
        self.assertEqual(comentario_nuevo.valoracion, 5)
        