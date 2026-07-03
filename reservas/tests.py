from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import date, timedelta
from django.contrib.auth import get_user_model
from catalogo.models import Categoria, Paquete, Temporada, Tarifa
from reservas.models import Reserva, Cancelacion

Usuario = get_user_model()

class ReservasYCancelacionesTestCase(TestCase):
    def setUp(self):
        """
        setUp.
        
        :return: Respuesta de la función.
        """
        # Crear usuario de prueba
        self.user = Usuario.objects.create_user(
            username='cliente_test',
            email='cliente@test.com',
            password='password123'
        )

        # Crear categoría y paquete de prueba
        self.categoria = Categoria.objects.create(
            nombre='Aventura',
            descripcion='Tours de aventura y adrenalina'
        )
        self.paquete = Paquete.objects.create(
            nombre='Parapente en Mongua',
            descripcion='Vuela sobre el hermoso valle',
            dias_duracion=1,
            noches_duracion=0,
            punto_encuentro='Plaza Principal',
            hora_encuentro=timezone.now().time(),
            categoria=self.categoria
        )

        # Crear temporada activa
        self.hoy = timezone.now().date()
        self.temporada = Temporada.objects.create(
            nombre='Temporada Alta 2026',
            fecha_inicio=self.hoy - timedelta(days=10),
            fecha_fin=self.hoy + timedelta(days=30),
            estado='activa'
        )

        # Crear tarifa para el paquete en la temporada
        self.tarifa = Tarifa.objects.create(
            paquete=self.paquete,
            temporada=self.temporada,
            precio_adulto=100000,
            precio_menor=50000,
            estado='activa'
        )

    def test_creacion_reserva_calculo_tarifa(self):
        """
        test_creacion_reserva_calculo_tarifa.
        
        :return: Respuesta de la función.
        """
        # Crear reserva para 2 adultos y 1 menor
        reserva = Reserva.objects.create(
            usuario=self.user,
            paquete=self.paquete,
            fecha=self.hoy,
            numero_adultos=2,
            numero_menores=1,
            estado='pendiente'
        )
        # Esperado: (100000 * 2) + (50000 * 1) = 250000
        self.assertEqual(reserva.monto_total, 250000)

    def test_reserva_duplicada_validation(self):
        """
        test_reserva_duplicada_validation.
        
        :return: Respuesta de la función.
        """
        # Crear la primera reserva
        Reserva.objects.create(
            usuario=self.user,
            paquete=self.paquete,
            fecha=self.hoy,
            numero_adultos=1,
            numero_menores=0
        )

        # Intentar crear una segunda para el mismo usuario, paquete y fecha
        reserva_duplicada = Reserva(
            usuario=self.user,
            paquete=self.paquete,
            fecha=self.hoy,
            numero_adultos=1,
            numero_menores=0
        )
        
        # Debe lanzar una ValidationError en el clean()
        with self.assertRaises(ValidationError):
            reserva_duplicada.full_clean()

    def test_cancelacion_penalidad_mas_de_15_dias(self):
        """
        test_cancelacion_penalidad_mas_de_15_dias.
        
        :return: Respuesta de la función.
        """
        # Reserva viaja en 20 días
        fecha_reserva = self.hoy + timedelta(days=20)
        reserva = Reserva.objects.create(
            usuario=self.user,
            paquete=self.paquete,
            fecha=fecha_reserva,
            numero_adultos=1,
            numero_menores=0
        )
        # Monto = 100000
        self.assertEqual(reserva.monto_total, 100000)

        # Crear solicitud de cancelación (hoy)
        cancelacion = Cancelacion.objects.create(
            reserva=reserva,
            motivo='Cambio de planes',
            estado='pendiente'
        )
        # >15 días: penalidad 10% del total = 10000
        self.assertEqual(cancelacion.penalidad, 10000)

    def test_cancelacion_penalidad_entre_5_y_15_dias(self):
        """
        test_cancelacion_penalidad_entre_5_y_15_dias.
        
        :return: Respuesta de la función.
        """
        # Reserva viaja en 10 días
        fecha_reserva = self.hoy + timedelta(days=10)
        reserva = Reserva.objects.create(
            usuario=self.user,
            paquete=self.paquete,
            fecha=fecha_reserva,
            numero_adultos=1,
            numero_menores=0
        )
        
        cancelacion = Cancelacion.objects.create(
            reserva=reserva,
            motivo='Fuerza mayor',
            estado='pendiente'
        )
        # Entre 5 y 15 días: penalidad 50% = 50000
        self.assertEqual(cancelacion.penalidad, 50000)

    def test_cancelacion_penalidad_menos_de_5_dias(self):
        """
        test_cancelacion_penalidad_menos_de_5_dias.
        
        :return: Respuesta de la función.
        """
        # Reserva viaja en 2 días
        fecha_reserva = self.hoy + timedelta(days=2)
        reserva = Reserva.objects.create(
            usuario=self.user,
            paquete=self.paquete,
            fecha=fecha_reserva,
            numero_adultos=1,
            numero_menores=0
        )
        
        cancelacion = Cancelacion.objects.create(
            reserva=reserva,
            motivo='Cancelación de último minuto',
            estado='pendiente'
        )
        # < 5 días: penalidad 100% = 100000
        self.assertEqual(cancelacion.penalidad, 100000)

    def test_flujo_estados_cancelacion(self):
        """
        test_flujo_estados_cancelacion.
        
        :return: Respuesta de la función.
        """
        reserva = Reserva.objects.create(
            usuario=self.user,
            paquete=self.paquete,
            fecha=self.hoy + timedelta(days=20),
            numero_adultos=1,
            numero_menores=0,
            estado='pendiente'
        )
        
        cancelacion = Cancelacion.objects.create(
            reserva=reserva,
            motivo='Prueba estado',
            estado='pendiente'
        )
        
        # Al aceptar la cancelación, la reserva debe cambiar a 'cancelada'
        cancelacion.estado = 'aceptada'
        cancelacion.save()
        reserva.refresh_from_db()
        self.assertEqual(reserva.estado, 'cancelada')
