from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django_tenants.utils import get_tenant_domain_model
from django.db import connection

class TenantASGIMiddleware(BaseMiddleware):
    """
    Middleware ASGI para detectar el inquilino (tenant) basado en el subdominio
    antes de procesar la conexión WebSocket.
    """
    async def __call__(self, scope, receive, send):
        # 1. Obtener el host de los headers
        headers = dict(scope['headers'])
        host = headers.get(b'host', b'').decode().split(':')[0]

        # 2. Buscar el tenant y activar el esquema
        try:
            tenant = await self.get_tenant(host)
            if tenant:
                scope['tenant'] = tenant
                # Activar el esquema en la conexión de BD para este hilo
                await self.set_schema(tenant.schema_name)
            else:
                print(f"⚠️ ASGI: No se encontró tenant para host {host}, usando public")
        except Exception as e:
            print(f"❌ Error en TenantASGIMiddleware: {e}")

        # 3. Continuar con la aplicación
        return await super().__call__(scope, receive, send)

    @database_sync_to_async
    def get_tenant(self, domain_name):
        Domain = get_tenant_domain_model()
        try:
            domain = Domain.objects.select_related('tenant').get(domain=domain_name)
            return domain.tenant
        except Domain.DoesNotExist:
            return None

    @database_sync_to_async
    def set_schema(self, schema_name):
        connection.set_schema(schema_name)