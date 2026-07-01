from django.test import TestCase
from django.apps import apps
from IA.apps import IAConfig

class IAConfigTest(TestCase):
    def test_ia_config_loaded(self):
        """Verifica que la configuración de la aplicación de IA esté cargada correctamente."""
        self.assertEqual(IAConfig.name, 'IA')
        app_config = apps.get_app_config('IA')
        self.assertIsInstance(app_config, IAConfig)
        self.assertEqual(app_config.name, 'IA')
