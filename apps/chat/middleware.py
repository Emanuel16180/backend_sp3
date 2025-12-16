# apps/chat/middleware.py
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from urllib.parse import parse_qs
User = get_user_model()

@database_sync_to_async  # <--- ¡UNA SOLA VEZ!
def get_user(token_key):
    try:
        token = Token.objects.get(key=token_key)
        # --- 3. CAMBIO ---
        # En lugar de devolver token.user (que puede ser perezoso),
        # buscamos al usuario completo por su ID para asegurar que funcione.
        user = User.objects.get(id=token.user_id)
        return user
        # --------------------
    except (Token.DoesNotExist, User.DoesNotExist):
        return AnonymousUser()
        

class TokenAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        # ... (el resto del archivo se queda igual)
        if scope.get("user") and scope["user"].is_authenticated:
            return await self.inner(scope, receive, send)

        query_string = scope.get("query_string", b"").decode("utf-8")
        query_params = parse_qs(query_string)
        token_key = query_params.get("token", [None])[0]

        if token_key:
            scope['user'] = await get_user(token_key)
        else:
            scope['user'] = AnonymousUser()
        
        return await self.inner(scope, receive, send)