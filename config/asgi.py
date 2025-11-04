# config/asgi.py
import os
import django
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from channels.auth import AuthMiddlewareStack
from apps.chat.middleware import TokenAuthMiddleware
import apps.chat.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(      # Primero intenta con la web (sesiones)
        TokenAuthMiddleware(              # Después, con el móvil (tokens)
            URLRouter(
                apps.chat.routing.websocket_urlpatterns
            )
        )
    ),
})