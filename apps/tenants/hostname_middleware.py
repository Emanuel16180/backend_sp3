# apps/tenants/hostname_middleware.py
import logging
from django_tenants.utils import get_tenant_model, get_tenant_domain_model

logger = logging.getLogger(__name__)

class HostnameDebugMiddleware:
    """
    Middleware para FORZAR detección correcta de tenant por hostname.
    Render NO envía X-Forwarded-Host, pero HTTP_HOST tiene el valor correcto.
    Este middleware detecta el tenant MANUALMENTE y lo establece en el request.
    DEBE ir ANTES de TenantMainMiddleware.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        hostname = request.get_host().split(':')[0].lower()
        
        logger.info(f"🔍 Detectando tenant para hostname: {hostname}")
        
        # Buscar el tenant correspondiente al hostname
        Domain = get_tenant_domain_model()
        Tenant = get_tenant_model()
        
        try:
            domain = Domain.objects.select_related('tenant').get(domain=hostname)
            tenant = domain.tenant
            
            # FORZAR el tenant en el request
            request.tenant = tenant
            
            logger.info(f"✅ Tenant detectado: {tenant.schema_name} (ID: {tenant.id})")
            logger.info(f"� Schema: {tenant.schema_name}")
            
        except Domain.DoesNotExist:
            logger.warning(f"⚠️ No se encontró dominio para: {hostname}")
            logger.warning(f"� Dominios disponibles: {list(Domain.objects.values_list('domain', flat=True))}")
        
        response = self.get_response(request)
        return response
