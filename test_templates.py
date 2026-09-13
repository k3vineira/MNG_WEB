import django
import os, glob
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()
from django.template.loader import get_template
from django.template.exceptions import TemplateSyntaxError, TemplateDoesNotExist

for f in glob.glob('App/templates/**/*.html', recursive=True):
    if os.path.isfile(f):
        name = os.path.relpath(f, 'App/templates').replace('\\', '/')
        try:
            get_template(name)
        except TemplateSyntaxError as e:
            print(f'SYNTAX ERROR in {name}: {e}')
        except TemplateDoesNotExist:
            pass
