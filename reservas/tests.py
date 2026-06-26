from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import date
from catalogo.models import Paquete, Temporada, Tarifa, Categoria
from .models import Reserva, Cancelacion

Usuario = get_user_model()

class MonaguaReservasTest(TestCase):

    def setUp(self):
        self.user = Usuario.objects.create_user(
            username="turista1",
            email="turista@gmail.com",
            password="password123"
        )
        self.categoria = Categoria.objects.create(
            nombre="EcoTurismo",
            descripcion="Planes ecológicos"
        )
        self.paquete = Paquete.objects.create(
            nombre="Páramo Ocetá",
            descripcion="Tour completo",
            punto_encuentro="Plaza",
            hora_encuentro=timezone.datetime.strptime("07:00", "%H:%M").time(),
            categoria=self.categoria
        )
        self.temporada = Temporada.objects.create(
            nombre="Temporada General",
            fecha_inicio=date(2026, 1, 1),
            fecha_fin=date(2026, 12, 31),
            estado="activa"
        )
        self.tarifa = Tarifa.objects.create(
            paquete=self.paquete,
            temporada=self.temporada,
            precio_adulto=100000,
            precio_menor=50000,
            estado="activa"
        )
        self.reserva = Reserva.objects.create(
            usuario=self.user,
            paquete=self.paquete,
            fecha=date(2026, 7, 20),
            numero_adultos=2,
            numero_menores=1,
            estado="pendiente"
        )

    def test_modelo_reserva_str(self):
        self.assertEqual(str(self.reserva), f"Reserva {self.reserva.id} - turista1 (Páramo Ocetá)")

    def test_calculo_monto_total_automatico(self):
        self.assertEqual(self.reserva.monto_total, 250000)

    def test_evitar_reserva_duplicada_mismo_dia(self):
        reserva_duplicada = Reserva(
            usuario=self.user,
            paquete=self.paquete,
            fecha=date(2026, 7, 20)
        )
        with self.assertRaises(ValidationError):
            reserva_duplicada.clean()

    def test_calculo_penalidad_alta_antelacion(self):
        cancelacion = Cancelacion.objects.create(
            reserva=self.reserva,
            motivo="Cambio de planes"
        )
        self.assertEqual(cancelacion.penalidad, 25000)

    def test_cambio_estado_reserva_al_aceptar_cancelacion(self):
        cancelacion = Cancelacion.objects.create(
            reserva=self.reserva,
            motivo="Salud",
            estado="aceptada"
        )
        self.reserva.refresh_from_db()
        self.assertEqual(self.reserva.estado, "cancelada")

    def test_modelo_cancelacion_str(self):
        cancelacion = Cancelacion.objects.create(
            reserva=self.reserva,
            motivo="Prueba"
        )
        self.assertEqual(str(cancelacion), f"Cancelación de Reserva #{self.reserva.id} - Pendiente")