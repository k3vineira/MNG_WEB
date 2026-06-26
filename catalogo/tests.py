import datetime
from django.test import TestCase
from catalogo.models import (
    Temporada, Categoria, Actividades,
    Paquete, Tarifa, PaqueteActividad
)


def crear_temporada(nombre='Temporada Test', estado='activa', dias_desde_hoy=0):
    """Helper: crea una temporada que cubre hoy por defecto."""
    from django.utils import timezone
    hoy = timezone.now().date()
    return Temporada.objects.create(
        nombre=nombre,
        fecha_inicio=hoy - datetime.timedelta(days=30 + dias_desde_hoy),
        fecha_fin=hoy + datetime.timedelta(days=30),
        estado=estado,
    )


def crear_categoria(nombre='Aventura'):
    return Categoria.objects.create(
        nombre=nombre,
        descripcion='Categoría de prueba',
        estado=True
    )


def crear_actividad(nombre='Senderismo', apto_menores=True):
    return Actividades.objects.create(
        nombre=nombre,
        descripcion='Descripción',
        nivel_dificultad='Media',
        equipo_requerimiento='Botas',
        recomendacion_salud='Ninguna',
        estado=True,
        apto_para_menores=apto_menores
    )


def crear_paquete(categoria=None, nombre='Paquete Test'):
    if categoria is None:
        categoria = crear_categoria()
    return Paquete.objects.create(
        nombre=nombre,
        descripcion='Descripción del paquete',
        dias_duracion=3,
        noches_duracion=2,
        punto_encuentro='Plaza Central',
        hora_encuentro=datetime.time(8, 0),
        categoria=categoria,
        estado=True
    )


# ──────────────────────────────────────────────────────────────────────────────
# TESTS DE TEMPORADA
# ──────────────────────────────────────────────────────────────────────────────

class TemporadaTest(TestCase):

    def test_crear_temporada(self):
        t = crear_temporada(nombre='Alta Temporada')
        self.assertEqual(t.nombre, 'Alta Temporada')
        self.assertEqual(t.estado, 'activa')

    def test_str_temporada(self):
        t = crear_temporada(nombre='Verano')
        self.assertEqual(str(t), 'Verano')

    def test_estado_default_programada(self):
        from django.utils import timezone
        hoy = timezone.now().date()
        t = Temporada.objects.create(
            nombre='Prog',
            fecha_inicio=hoy,
            fecha_fin=hoy + datetime.timedelta(days=10)
        )
        self.assertEqual(t.estado, 'programada')

    def test_choices_estado_validos(self):
        estados = [e[0] for e in Temporada.ESTADOS]
        self.assertIn('programada', estados)
        self.assertIn('activa', estados)
        self.assertIn('finalizada', estados)


# ──────────────────────────────────────────────────────────────────────────────
# TESTS DE CATEGORIA
# ──────────────────────────────────────────────────────────────────────────────

class CategoriaTest(TestCase):

    def test_crear_categoria(self):
        cat = crear_categoria('Cultural')
        self.assertEqual(cat.nombre, 'Cultural')
        self.assertTrue(cat.estado)

    def test_str_categoria(self):
        cat = crear_categoria('Playa')
        self.assertEqual(str(cat), 'Playa')

    def test_estado_default_activa(self):
        cat = Categoria.objects.create(nombre='Cat2', descripcion='Desc')
        self.assertTrue(cat.estado)


# ──────────────────────────────────────────────────────────────────────────────
# TESTS DE ACTIVIDADES
# ──────────────────────────────────────────────────────────────────────────────

class ActividadesTest(TestCase):

    def test_crear_actividad(self):
        act = crear_actividad('Kayak')
        self.assertEqual(act.nombre, 'Kayak')
        self.assertEqual(act.nivel_dificultad, 'Media')

    def test_str_actividad(self):
        act = crear_actividad('Ciclismo')
        self.assertEqual(str(act), 'Ciclismo')

    def test_apto_para_menores_default_true(self):
        act = crear_actividad()
        self.assertTrue(act.apto_para_menores)

    def test_nivel_dificultad_choices(self):
        niveles = [n[0] for n in Actividades.NIVEL_CHOICES]
        self.assertIn('Alta', niveles)
        self.assertIn('Media', niveles)
        self.assertIn('Baja', niveles)


# ──────────────────────────────────────────────────────────────────────────────
# TESTS DE PAQUETE
# ──────────────────────────────────────────────────────────────────────────────

class PaqueteTest(TestCase):

    def setUp(self):
        self.cat = crear_categoria()
        self.paquete = crear_paquete(self.cat, 'Tour Monagua')

    def test_crear_paquete(self):
        self.assertEqual(self.paquete.nombre, 'Tour Monagua')
        self.assertTrue(self.paquete.estado)

    def test_str_paquete(self):
        self.assertEqual(str(self.paquete), 'Tour Monagua')

    def test_precio_minimo_sin_tarifas_retorna_cero(self):
        self.assertEqual(self.paquete.precio_minimo, 0)

    def test_precio_minimo_con_tarifa_activa(self):
        temporada = crear_temporada(nombre='Estandar', estado='activa')
        Tarifa.objects.create(
            paquete=self.paquete,
            temporada=temporada,
            precio_adulto=150000,
            precio_menor=80000,
            estado='activa'
        )
        self.assertEqual(self.paquete.precio_minimo, 150000)

    def test_apto_para_menores_sin_actividades(self):
        # Sin actividades, no hay ninguna que bloquee, es apto
        self.assertTrue(self.paquete.apto_para_menores)

    def test_apto_para_menores_con_actividad_no_apta(self):
        act_no_apta = crear_actividad('Rappel', apto_menores=False)
        self.paquete.actividades.add(act_no_apta)
        self.assertFalse(self.paquete.apto_para_menores)


# ──────────────────────────────────────────────────────────────────────────────
# TESTS DE TARIFA
# ──────────────────────────────────────────────────────────────────────────────

class TarifaTest(TestCase):

    def setUp(self):
        self.paquete = crear_paquete()
        self.temporada = crear_temporada()

    def test_crear_tarifa(self):
        tarifa = Tarifa.objects.create(
            paquete=self.paquete,
            temporada=self.temporada,
            precio_adulto=200000,
            precio_menor=100000
        )
        self.assertEqual(tarifa.precio_adulto, 200000)
        self.assertEqual(tarifa.estado, 'activa')

    def test_str_tarifa(self):
        tarifa = Tarifa.objects.create(
            paquete=self.paquete,
            temporada=self.temporada,
            precio_adulto=200000,
            precio_menor=100000
        )
        self.assertIn(self.paquete.nombre, str(tarifa))
        self.assertIn(self.temporada.nombre, str(tarifa))

    def test_unique_paquete_temporada(self):
        Tarifa.objects.create(
            paquete=self.paquete,
            temporada=self.temporada,
            precio_adulto=200000,
            precio_menor=100000
        )
        with self.assertRaises(Exception):
            Tarifa.objects.create(
                paquete=self.paquete,
                temporada=self.temporada,
                precio_adulto=300000,
                precio_menor=150000
            )


# ──────────────────────────────────────────────────────────────────────────────
# TESTS DE PAQUETEACTIVIDAD
# ──────────────────────────────────────────────────────────────────────────────

class PaqueteActividadTest(TestCase):

    def test_asociar_actividad_a_paquete(self):
        paquete = crear_paquete()
        actividad = crear_actividad('Tirolesa')
        PaqueteActividad.objects.create(paquete=paquete, actividad=actividad)
        self.assertIn(actividad, paquete.actividades.all())

    def test_multiples_actividades_en_paquete(self):
        paquete = crear_paquete()
        act1 = crear_actividad('Senderismo')
        act2 = crear_actividad('Ciclismo')
        PaqueteActividad.objects.create(paquete=paquete, actividad=act1)
        PaqueteActividad.objects.create(paquete=paquete, actividad=act2)
        self.assertEqual(paquete.actividades.count(), 2)
