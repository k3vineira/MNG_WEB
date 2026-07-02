import datetime
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from catalogo.models import Categoria, Paquete
from promociones.models import Promocion, Banner

class PromocionesTestCase(TestCase):
    def setUp(self):
        """
        setUp.
        
        :return: Respuesta de la función.
        """
        # Crear categoría y paquete para la promoción
        self.categoria = Categoria.objects.create(
            nombre='Playas',
            descripcion='Tours de playa'
        )
        self.paquete = Paquete.objects.create(
            nombre='Especial Cartagena',
            descripcion='Tour por la ciudad amurallada',
            dias_duracion=3,
            noches_duracion=2,
            punto_encuentro='Aeropuerto',
            hora_encuentro=datetime.time(10, 0),
            categoria=self.categoria
        )

    def test_crear_promocion(self):
        """
        test_crear_promocion.
        
        :return: Respuesta de la función.
        """
        fecha_fin = timezone.now().date() + datetime.timedelta(days=7)
        promo = Promocion.objects.create(
            paquete=self.paquete,
            nombre='Descuento de Temporada',
            descripcion='Disfruta de Cartagena con un 15% de descuento.',
            descuento=15,
            fecha_fin=fecha_fin,
            activa=True
        )
        self.assertEqual(promo.nombre, 'Descuento de Temporada')
        self.assertEqual(promo.descuento, 15)
        self.assertTrue(promo.activa)
        self.assertEqual(str(promo), 'Descuento de Temporada (15%)')

    def test_crear_banner(self):
        """
        test_crear_banner.
        
        :return: Respuesta de la función.
        """
        banner = Banner.objects.create(
            imagen='banners/test_banner.jpg',
            titulo='Banner Principal',
            enlace='https://example.com/promo',
            activo=True
        )
        self.assertEqual(banner.titulo, 'Banner Principal')
        self.assertEqual(banner.enlace, 'https://example.com/promo')
        self.assertTrue(banner.activo)
        self.assertEqual(str(banner), 'Banner Principal')

    def test_gestion_promociones_view(self):
        """
        test_gestion_promociones_view.
        
        :return: Respuesta de la función.
        """
        fecha_fin = timezone.now().date() + datetime.timedelta(days=5)
        Promocion.objects.create(
            paquete=self.paquete,
            nombre='Super Promo',
            descripcion='Super descuento',
            descuento=20,
            fecha_fin=fecha_fin,
            activa=True
        )
        response = self.client.get(reverse('gestion_promociones'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Super Promo')
        self.assertContains(response, 'Ofertas de Temporada')
