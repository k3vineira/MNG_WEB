from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, time
from .models import Temporada, Categoria, Actividades, Paquete, Tarifa, PaqueteActividad

class MonaguaModelosTest(TestCase):

    def setUp(self):
        self.temporada = Temporada.objects.create(
            nombre="Alta Verano",
            fecha_inicio=date(2026, 6, 1),
            fecha_fin=date(2026, 8, 31),
            estado="activa"
        )
        self.categoria = Categoria.objects.create(
            nombre="Senderismo",
            descripcion="Caminatas por la naturaleza",
            estado=True
        )
        self.actividad_1 = Actividades.objects.create(
            nombre="Caminata Páramo",
            descripcion="Recorrido guiado",
            nivel_dificultad="Media",
            equipo_requerimiento="Botas",
            recomendacion_salud="Ninguna",
            estado=True,
            apto_para_menores=True
        )
        self.actividad_2 = Actividades.objects.create(
            nombre="Escalada Roca",
            descripcion="Escalada avanzada",
            nivel_dificultad="Alta",
            equipo_requerimiento="Arnés",
            recomendacion_salud="Buen estado físico",
            estado=True,
            apto_para_menores=False
        )
        self.paquete = Paquete.objects.create(
            nombre="Aventura Ocetá",
            descripcion="Tour completo",
            dias_duracion=2,
            noches_duracion=1,
            punto_encuentro="Plaza de Mongua",
            hora_encuentro=time(7, 0),
            categoria=self.categoria,
            estado=True
        )
        PaqueteActividad.objects.create(paquete=self.paquete, actividad=self.actividad_1)
        PaqueteActividad.objects.create(paquete=self.paquete, actividad=self.actividad_2)
        
        self.tarifa = Tarifa.objects.create(
            paquete=self.paquete,
            temporada=self.temporada,
            precio_adulto=120000,
            precio_menor=80000,
            estado="activa"
        )

    def test_modelo_temporada_str(self):
        self.assertEqual(str(self.temporada), "Alta Verano")

    def test_temporada_estado_invalido(self):
        self.temporada.estado = "invalido"
        with self.assertRaises(ValidationError):
            self.temporada.full_clean()

    def test_modelo_categoria_str(self):
        self.assertEqual(str(self.categoria), "Senderismo")

    def test_modelo_actividades_str(self):
        self.assertEqual(str(self.actividad_1), "Caminata Páramo")

    def test_actividades_dificultad_invalida(self):
        self.actividad_1.nivel_dificultad = "Extrema"
        with self.assertRaises(ValidationError):
            self.actividad_1.full_clean()

    def test_modelo_paquete_str(self):
        self.assertEqual(str(self.paquete), "Aventura Ocetá")

    def test_paquete_no_apto_para_menores(self):
        self.assertFalse(self.paquete.apto_para_menores)

    def test_paquete_precio_minimo_calculado(self):
        self.assertEqual(self.paquete.precio_minimo, 120000)

    def test_modelo_tarifa_str(self):
        esperado = "Aventura Ocetá - Alta Verano"
        self.assertEqual(str(self.tarifa), esperado)

    def test_tarifa_valores_unicos(self):
        with self.assertRaises(Exception):
            Tarifa.objects.create(
                paquete=self.paquete,
                temporada=self.temporada,
                precio_adulto=100000,
                precio_menor=60000
            )