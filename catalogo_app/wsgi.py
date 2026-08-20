"""WSGI config for catalogo_app project."""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'catalogo_app.settings')
application = get_wsgi_application()
