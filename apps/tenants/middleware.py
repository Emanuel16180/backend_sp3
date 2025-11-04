# apps/tenants/middleware.py

from django.db import connection
from django.conf import settings
from django.urls import clear_url_caches
from django.utils.deprecation import MiddlewareMixin

class TenantAdminTitleMiddleware(MiddlewareMixin):
    """
    Middleware que fuerza el cambio de URLconf según el tenant
    Ya no necesita modificar títulos porque tenemos admin sites separados
    """
    
    def process_request(self, request):
        """
        Procesar request ANTES de que llegue a las views
        """
        # Verificar si tenemos un tenant y forzar URLconf si es necesario
        if hasattr(connection, 'tenant') and connection.tenant:
            if connection.tenant.schema_name == 'public':
                # Para tenant público: usar ROOT_URLCONF
                request.urlconf = settings.ROOT_URLCONF
                clear_url_caches()
            else:
                # Para tenants individuales: usar TENANT_URLCONF
                request.urlconf = settings.TENANT_URLCONF
                clear_url_caches()
        
        return None