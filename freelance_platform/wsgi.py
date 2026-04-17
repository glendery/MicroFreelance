"""
WSGI config for freelance_platform project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'freelance_platform.settings')

application = get_wsgi_application()

# Run collectstatic if on Vercel
if os.environ.get('VERCEL'):
    from django.core.management import call_command
    try:
        call_command('collectstatic', '--noinput', '--clear')
    except Exception:
        pass

# Alias for Vercel
app = application
