from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from catalogo.models import Categoria, Actividades, Paquete, Temporada, Tarifa

class CatalogoTestCase(TestCase):
    def setUp(self):
        # Crear categoría
        self.categoria = Categoria.objects.create(
            nombre='Cultura',
            descripcion='Tours de museos, historia y arte local'
        )

        # Crear actividades
        self.actividad_apta = Actividades.objects.create(
            nombre='Caminata guiada',
            descripcion='Paseo por las calles históricas',
            nivel_dificultad='Baja',
            equipo_requerimiento='Zapatos cómodos',
            recomendacion_salud='Ninguna',
            apto_para_menores=True
        )
        self.actividad_no_apta = Actividades.objects.create(
            nombre='Escalada extrema',
            descripcion='Escalada vertical en roca',
            nivel_dificultad='Alta',
            equipo_requerimiento='Arnés, casco',
            recomendacion_salud='No apto para problemas cardíacos',
            apto_para_menores=False
        )

    def test_paquete_apto_para_menores(self):
        # Paquete que sólo contiene la actividad apta para menores
        paquete_familiar = Paquete.objects.create(
            nombre='Mongua Familiar',
            descripcion='Disfruta en familia',
            dias_duracion=1,
            noches_duracion=0,
            punto_encuentro='Plaza',
            hora_encuentro='09:00:00',
            categoria=self.categoria
        )
        paquete_familiar.actividades.add(self.actividad_apta)
        self.assertTrue(paquete_familiar.apto_para_menores)

        # Paquete que contiene una actividad no apta para menores
        paquete_extremo = Paquete.objects.create(
            nombre='Mongua Extremo',
            descripcion='Adrenalina pura',
            dias_duracion=1,
            noches_duracion=0,
            punto_encuentro='Plaza',
            hora_encuentro='07:00:00',
            categoria=self.categoria
        )
        paquete_extremo.actividades.add(self.actividad_apta)
        paquete_extremo.actividades.add(self.actividad_no_apta)
        
        # Debe retornar False debido a la actividad extrema
        self.assertFalse(paquete_extremo.apto_para_menores)

    def test_precio_minimo_calculo(self):
        paquete = Paquete.objects.create(
            nombre='Tour Histórico',
            descripcion='Descripción corta',
            dias_duracion=1,
            noches_duracion=0,
            punto_encuentro='Plaza',
            hora_encuentro='10:00:00',
            categoria=self.categoria
        )

        # Crear temporada actual activa
        hoy = timezone.now().date()
        temporada_alta = Temporada.objects.create(
            nombre='Temporada Alta Actual',
            fecha_inicio=hoy - timedelta(days=5),
            fecha_fin=hoy + timedelta(days=5),
            estado='activa'
        )

        # Crear tarifa activa
        Tarifa.objects.create(
            paquete=paquete,
            temporada=temporada_alta,
            precio_adulto=75000,
            precio_menor=40000,
            estado='activa'
        )

        # El precio mínimo debe ser 75000 (el precio del adulto para la tarifa activa de hoy)
        self.assertEqual(paquete.precio_minimo, 75000)
