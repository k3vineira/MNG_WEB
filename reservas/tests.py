import datetime
from django.test import TestCase
from django.utils import timezone
from usuarios.models import Usuario
from catalogo.models import Categoria, Paquete, Temporada, Tarifa
from reservas.models import Reserva, Cancelacion
from django.core.exceptions import ValidationError


def crear_usuario(username='testuser'):
    return Usuario.objects.create_user(
        username=username,
        password='pass123',
        email=f'{username}@test.com'
    )


def crear_paquete(nombre='Paquete Test'):
    cat = Categoria.objects.create(nombre='Cat', descripcion='Desc')
    return Paquete.objects.create(
        nombre=nombre,
        descripcion='Desc',
        dias_duracion=2,
        noches_duracion=1,
        punto_encuentro='Plaza',
        hora_encuentro=datetime.time(9, 0),
        categoria=cat
    )


def crear_temporada_con_tarifa(paquete):
    hoy = timezone.now().date()
    temporada = Temporada.objects.create(
        nombre='Temporada Activa',
        fecha_inicio=hoy - datetime.timedelta(days=5),
        fecha_fin=hoy + datetime.timedelta(days=30),
        estado='activa'
    )
    Tarifa.objects.create(
        paquete=paquete,
        temporada=temporada,
        precio_adulto=200000,
        precio_menor=100000,
        estado='activa'
    )
    return temporada


def crear_reserva(usuario, paquete, fecha=None, adultos=1, menores=0):
    if fecha is None:
        fecha = timezone.now().date() + datetime.timedelta(days=30)
    return Reserva.objects.create(
        usuario=usuario,
        paquete=paquete,
        fecha=fecha,
        numero_adultos=adultos,
        numero_menores=menores
    )


# ──────────────────────────────────────────────────────────────────────────────
# TESTS DE RESERVA
# ──────────────────────────────────────────────────────────────────────────────

class ReservaCreacionTest(TestCase):

    def setUp(self):
        self.usuario = crear_usuario()
        self.paquete = crear_paquete()

    def test_crear_reserva_estado_pendiente(self):
        reserva = crear_reserva(self.usuario, self.paquete)
        self.assertEqual(reserva.estado, 'pendiente')
        self.assertTrue(reserva.pk)

    def test_crear_reserva_calcula_monto_con_tarifa(self):
        crear_temporada_con_tarifa(self.paquete)
        reserva = crear_reserva(self.usuario, self.paquete, adultos=2, menores=1)
        # 2 adultos x 200.000 + 1 menor x 100.000 = 500.000
        self.assertEqual(reserva.monto_total, 500000)

    def test_crear_reserva_monto_cero_sin_tarifa(self):
        reserva = crear_reserva(self.usuario, self.paquete)
        self.assertEqual(reserva.monto_total, 0)

    def test_str_reserva(self):
        reserva = crear_reserva(self.usuario, self.paquete)
        resultado = str(reserva)
        self.assertIn(str(reserva.id), resultado)
        self.assertIn(self.paquete.nombre, resultado)

    def test_numero_adultos_default_uno(self):
        reserva = crear_reserva(self.usuario, self.paquete)
        self.assertEqual(reserva.numero_adultos, 1)

    def test_numero_menores_default_cero(self):
        reserva = crear_reserva(self.usuario, self.paquete)
        self.assertEqual(reserva.numero_menores, 0)


class ReservaUnicidadTest(TestCase):

    def setUp(self):
        self.usuario = crear_usuario('u_unico')
        self.paquete = crear_paquete('Unico')
        self.fecha = timezone.now().date() + datetime.timedelta(days=20)

    def test_unique_constraint_usuario_paquete_fecha(self):
        crear_reserva(self.usuario, self.paquete, fecha=self.fecha)
        with self.assertRaises(Exception):
            crear_reserva(self.usuario, self.paquete, fecha=self.fecha)

    def test_diferente_fecha_permite_segunda_reserva(self):
        fecha1 = timezone.now().date() + datetime.timedelta(days=10)
        fecha2 = timezone.now().date() + datetime.timedelta(days=20)
        r1 = crear_reserva(self.usuario, self.paquete, fecha=fecha1)
        r2 = crear_reserva(self.usuario, self.paquete, fecha=fecha2)
        self.assertNotEqual(r1.pk, r2.pk)


class ReservaEstadosTest(TestCase):

    def setUp(self):
        self.usuario = crear_usuario('estado_user')
        self.paquete = crear_paquete('Paquete Estado')

    def test_choices_estado_validos(self):
        estados = [e[0] for e in Reserva.ESTADO_CHOICES]
        self.assertIn('pendiente', estados)
        self.assertIn('confirmada', estados)
        self.assertIn('cancelada', estados)

    def test_cambiar_estado_a_confirmada(self):
        reserva = crear_reserva(self.usuario, self.paquete)
        reserva.estado = 'confirmada'
        reserva.save()
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, 'confirmada')


# ──────────────────────────────────────────────────────────────────────────────
# TESTS DE CANCELACION
# ──────────────────────────────────────────────────────────────────────────────

class CancelacionTest(TestCase):

    def setUp(self):
        self.usuario = crear_usuario('cancel_user')
        self.paquete = crear_paquete('Paquete Cancelar')
        crear_temporada_con_tarifa(self.paquete)

    def _reserva_con_fecha(self, dias_desde_hoy):
        fecha = timezone.now().date() + datetime.timedelta(days=dias_desde_hoy)
        return crear_reserva(self.usuario, self.paquete, fecha=fecha, adultos=1)

    def test_cancelacion_mas_de_15_dias_penalidad_10_pct(self):
        reserva = self._reserva_con_fecha(20)
        cancelacion = Cancelacion.objects.create(reserva=reserva, motivo='Prueba')
        esperado = int(reserva.monto_total * 0.10)
        self.assertEqual(cancelacion.penalidad, esperado)

    def test_cancelacion_entre_5_y_15_dias_penalidad_50_pct(self):
        reserva = self._reserva_con_fecha(10)
        cancelacion = Cancelacion.objects.create(reserva=reserva, motivo='Prueba')
        esperado = int(reserva.monto_total * 0.50)
        self.assertEqual(cancelacion.penalidad, esperado)

    def test_cancelacion_menos_de_5_dias_penalidad_total(self):
        reserva = self._reserva_con_fecha(3)
        cancelacion = Cancelacion.objects.create(reserva=reserva, motivo='Prueba')
        self.assertEqual(cancelacion.penalidad, reserva.monto_total)

    def test_estado_aceptada_cancela_reserva(self):
        reserva = self._reserva_con_fecha(20)
        cancelacion = Cancelacion.objects.create(reserva=reserva, motivo='Prueba')
        cancelacion.estado = 'aceptada'
        cancelacion.save()
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, 'cancelada')

    def test_estado_rechazada_confirma_reserva(self):
        reserva = self._reserva_con_fecha(20)
        cancelacion = Cancelacion.objects.create(reserva=reserva, motivo='Prueba')
        cancelacion.estado = 'rechazada'
        cancelacion.save()
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, 'confirmada')

    def test_str_cancelacion(self):
        reserva = self._reserva_con_fecha(20)
        cancelacion = Cancelacion.objects.create(reserva=reserva, motivo='Prueba')
        self.assertIn(str(reserva.id), str(cancelacion))

    def test_choices_estado_cancelacion(self):
        estados = [e[0] for e in Cancelacion.ESTADOS_CANCELACION]
        self.assertIn('pendiente', estados)
        self.assertIn('aceptada', estados)
        self.assertIn('rechazada', estados)
