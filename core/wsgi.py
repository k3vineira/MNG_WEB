"""
Configuración WSGI del proyecto para despliegue en servidores compatibles con WSGI.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = get_wsgi_application()
