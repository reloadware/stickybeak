"""
WSGI config for django_srv project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/howto/deployment/wsgi/
"""

import os
from pathlib import Path

from django.core.wsgi import get_wsgi_application

import stickybeak

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "django_srv.settings")

application = get_wsgi_application()

stickybeak_port = int(os.environ["STICKYBEAK_PORT"])
timeout = os.environ.get("STICKYBEAK_TIMEOUT")
timeout = float(timeout) if timeout else None

stickybeak.Server(project_root=Path(os.getcwd()), port=stickybeak_port, timeout=timeout).run()
