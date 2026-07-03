import datetime
from django.test import TestCase
from django.utils import timezone
from usuarios.models import Usuario
from catalogo.models import Categoria, Paquete, Temporada, Tarifa
from reservas.models import Reserva
from pagos.models import ComprobantePago


def crear_usuario(username='pago_user'):
    """
    crear_usuario.
    
    :param username='pago_user': Descripción del parámetro.
    
    :return: Respuesta de la función.
    """
    return Usuario.objects.create_user(
        username=username,
        password='pass123',
        email=f'{username}@test.com'
    )


def crear_paquete():
    """
    crear_paquete.
    
    :return: Respuesta de la función.
    """
    cat = Categoria.objects.create(nombre='Cat Pagos', descripcion='Desc')
    return Paquete.objects.create(
        nombre='Paquete Pagos',
        descripcion='Desc',
        dias_duracion=2,
        noches_duracion=1,
        punto_encuentro='Plaza',
        hora_encuentro=datetime.time(9, 0),
        categoria=cat
    )


def crear_reserva(usuario, paquete):
    """
    crear_reserva.
    
    :param usuario: Descripción del parámetro.
    
    :param paquete: Descripción del parámetro.
    
    :return: Respuesta de la función.
    """
    fecha = timezone.now().date() + datetime.timedelta(days=30)
    return Reserva.objects.create(
        usuario=usuario,
        paquete=paquete,
        fecha=fecha,
        numero_adultos=1
    )


# ──────────────────────────────────────────────────────────────────────────────
# TESTS DE COMPROBANTE DE PAGO
# ──────────────────────────────────────────────────────────────────────────────

class ComprobantePagoCreacionTest(TestCase):

    def setUp(self):
        """
        setUp.
        
        :return: Respuesta de la función.
        """
        self.usuario = crear_usuario()
        self.paquete = crear_paquete()
        self.reserva = crear_reserva(self.usuario, self.paquete)

    def test_crear_comprobante_estado_pendiente(self):
        """
        test_crear_comprobante_estado_pendiente.
        
        :return: Respuesta de la función.
        """
        comp = ComprobantePago.objects.create(
            usuario=self.usuario,
            reserva=self.reserva,
            referencia='REF-001',
            banco_origen='Bancolombia',
            monto=200000,
            imagen='comprobantes/test.jpg',
            descripcion='Pago de prueba'
        )
        self.assertEqual(comp.estado, 'pendiente')
        self.assertTrue(comp.pk)

    def test_str_comprobante(self):
        """
        test_str_comprobante.
        
        :return: Respuesta de la función.
        """
        comp = ComprobantePago.objects.create(
            usuario=self.usuario,
            imagen='comprobantes/test.jpg'
        )
        resultado = str(comp)
        self.assertIn(self.usuario.username, resultado)
        self.assertIn('Pendiente', resultado)

    def test_estado_default_pendiente(self):
        """
        test_estado_default_pendiente.
        
        :return: Respuesta de la función.
        """
        comp = ComprobantePago.objects.create(
            usuario=self.usuario,
            imagen='comprobantes/test.jpg'
        )
        self.assertEqual(comp.estado, 'pendiente')

    def test_monto_puede_ser_nulo(self):
        """
        test_monto_puede_ser_nulo.
        
        :return: Respuesta de la función.
        """
        comp = ComprobantePago.objects.create(
            usuario=self.usuario,
            imagen='comprobantes/test.jpg',
            monto=None
        )
        self.assertIsNone(comp.monto)

    def test_reserva_puede_ser_nula(self):
        """
        test_reserva_puede_ser_nula.
        
        :return: Respuesta de la función.
        """
        comp = ComprobantePago.objects.create(
            usuario=self.usuario,
            imagen='comprobantes/test.jpg',
            reserva=None
        )
        self.assertIsNone(comp.reserva)


class ComprobantePagoEstadosTest(TestCase):

    def setUp(self):
        """
        setUp.
        
        :return: Respuesta de la función.
        """
        self.usuario = crear_usuario('estado_pago')

    def test_choices_estado_validos(self):
        """
        test_choices_estado_validos.
        
        :return: Respuesta de la función.
        """
        estados = [e[0] for e in ComprobantePago.ESTADO_CHOICES]
        self.assertIn('pendiente', estados)
        self.assertIn('aprobado', estados)
        self.assertIn('rechazado', estados)

    def test_cambiar_estado_a_aprobado(self):
        """
        test_cambiar_estado_a_aprobado.
        
        :return: Respuesta de la función.
        """
        comp = ComprobantePago.objects.create(
            usuario=self.usuario,
            imagen='comprobantes/test.jpg'
        )
        comp.estado = 'aprobado'
        comp.save()
        comp.refresh_from_db()
        self.assertEqual(comp.estado, 'aprobado')

    def test_cambiar_estado_a_rechazado(self):
        """
        test_cambiar_estado_a_rechazado.
        
        :return: Respuesta de la función.
        """
        comp = ComprobantePago.objects.create(
            usuario=self.usuario,
            imagen='comprobantes/test.jpg'
        )
        comp.estado = 'rechazado'
        comp.save()
        comp.refresh_from_db()
        self.assertEqual(comp.estado, 'rechazado')

    def test_nombre_archivo_sin_imagen(self):
        """
        test_nombre_archivo_sin_imagen.
        
        :return: Respuesta de la función.
        """
        comp = ComprobantePago.objects.create(
            usuario=self.usuario,
            imagen='comprobantes/recibo.jpg'
        )
        # El método nombre_archivo debe retornar el basename
        self.assertEqual(comp.nombre_archivo(), 'recibo.jpg')

    def test_ordenamiento_por_fecha_envio_descendente(self):
        """
        test_ordenamiento_por_fecha_envio_descendente.
        
        :return: Respuesta de la función.
        """
        comp1 = ComprobantePago.objects.create(
            usuario=self.usuario,
            imagen='comprobantes/a.jpg'
        )
        comp2 = ComprobantePago.objects.create(
            usuario=self.usuario,
            imagen='comprobantes/b.jpg'
        )
        comprobantes = list(ComprobantePago.objects.all())
        self.assertEqual(comprobantes[0].pk, comp2.pk)

    def test_relacion_usuario_comprobante(self):
        """
        test_relacion_usuario_comprobante.
        
        :return: Respuesta de la función.
        """
        comp = ComprobantePago.objects.create(
            usuario=self.usuario,
            imagen='comprobantes/test.jpg'
        )
        self.assertIn(comp, self.usuario.comprobantes.all())
