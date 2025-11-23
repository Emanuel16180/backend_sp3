import os
import django
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from apps.chat.middleware import TokenAuthMiddleware
import apps.chat.routing

# --- IMPORTA TU NUEVO MIDDLEWARE ---
from apps.tenants.asgi_middleware import TenantASGIMiddleware 

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    
    # Envuelve todo el stack de WebSocket con TenantASGIMiddleware
    "websocket": TenantASGIMiddleware( 
        AuthMiddlewareStack(
            TokenAuthMiddleware(
                URLRouter(
                    apps.chat.routing.websocket_urlpatterns
                )
            )
        )
    ),
})