from django.test import TestCase, Client
from django.urls import reverse
from App.models import Usuario
from autenticacion.forms import RegistroForm
from autenticacion.geografia import (
    get_paises,
    get_departamentos,
    get_ciudades,
    get_nombre_pais,
    get_nombre_departamento,
    get_nombre_ciudad,
)


class GeografiaLocalTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    def test_geografia_dataset_cargado(self):
        """Verifica que el dataset dr5hn se cargue correctamente en memoria."""
        paises = get_paises()
        self.assertGreaterEqual(len(paises), 240)

        # Verificar Colombia
        colombia = next((p for p in paises if p['iso3'] == 'COL'), None)
        self.assertIsNotNone(colombia)
        self.assertEqual(colombia['name'], 'Colombia')

        # Verificar departamentos de Colombia
        deps = get_departamentos('COL')
        self.assertGreaterEqual(len(deps), 30)

        boyaca = next((d for d in deps if 'boyac' in d['name'].lower()), None)
        self.assertIsNotNone(boyaca)

        # Verificar municipios de Boyacá (debe contener Mongua)
        ciudades_boyaca = get_ciudades(boyaca['id'])
        self.assertGreater(len(ciudades_boyaca), 50)
        mongua = next((c for c in ciudades_boyaca if 'mongua' in c['name'].lower()), None)
        self.assertIsNotNone(mongua)

    def test_resolucion_de_nombres_geograficos(self):
        """Verifica que las funciones de resolución de texto retornen nombres correctos."""
        self.assertEqual(get_nombre_pais('COL'), 'Colombia')
        self.assertEqual(get_nombre_pais('CO'), 'Colombia')

        deps = get_departamentos('COL')
        boyaca = next((d for d in deps if 'boyac' in d['name'].lower()), None)
        self.assertIn('boyac', get_nombre_departamento(boyaca['id']).lower())

        ciudades_boyaca = get_ciudades(boyaca['id'])
        mongua = next((c for c in ciudades_boyaca if 'mongua' in c['name'].lower()), None)
        self.assertEqual(get_nombre_ciudad(mongua['id']), 'Mongua')

    def test_api_endpoints_geografia(self):
        """Comprueba que las rutas REST respondan 200 con formato JSON válido."""
        # 1. API Países
        resp_paises = self.client.get(reverse('api_paises'))
        self.assertEqual(resp_paises.status_code, 200)
        data_paises = resp_paises.json()
        self.assertIsInstance(data_paises, list)
        self.assertGreaterEqual(len(data_paises), 240)

        # 2. API Departamentos
        resp_deps = self.client.get(reverse('api_departamentos', args=['COL']))
        self.assertEqual(resp_deps.status_code, 200)
        data_deps = resp_deps.json()
        self.assertIsInstance(data_deps, list)
        boyaca = next((d for d in data_deps if 'boyac' in d['name'].lower()), None)
        self.assertIsNotNone(boyaca)

        # 3. API Ciudades
        resp_ciudades = self.client.get(reverse('api_ciudades', args=[boyaca['id']]))
        self.assertEqual(resp_ciudades.status_code, 200)
        data_ciudades = resp_ciudades.json()
        self.assertIsInstance(data_ciudades, list)
        mongua = next((c for c in data_ciudades if 'mongua' in c['name'].lower()), None)
        self.assertIsNotNone(mongua)

    def test_propiedades_usuario_geografia(self):
        """Comprueba que un usuario con IDs dr5hn resuelva correctamente sus nombres y cliente."""
        deps = get_departamentos('COL')
        boyaca = next((d for d in deps if 'boyac' in d['name'].lower()), None)
        ciudades_boyaca = get_ciudades(boyaca['id'])
        mongua = next((c for c in ciudades_boyaca if 'mongua' in c['name'].lower()), None)

        user = Usuario.objects.create(
            username='turista_dr5hn_test',
            email='turista@monagua.test',
            tipo_documento='CC',
            numero_documento='9998887771',
            telefono='3001112233',
            pais='COL',
            departamento=boyaca['id'],
            ciudad=mongua['id'],
            rol=Usuario.Roles.CLIENTE
        )

        self.assertEqual(user.cliente, user)
        self.assertEqual(user.nombre_pais, 'Colombia')
        self.assertIn('boyac', user.nombre_departamento.lower())
        self.assertEqual(user.nombre_ciudad, 'Mongua')
