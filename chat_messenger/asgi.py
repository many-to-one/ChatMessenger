"""
ASGI config for qwe project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""

import os
import django
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from core.consumers import *
from core import routing
from django.urls import path

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat_messenger.settings')
# django.setup()

# Import Django settings after configuring the module
from django.conf import settings

# Now you can access Django settings
print(settings.DEBUG)










application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": 
        AuthMiddlewareStack(URLRouter(routing.websocket_urlpatterns)),
})
