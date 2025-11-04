# apps/tenants/custom_tenant_middleware.py
import logging
from django.db import connection
from django_tenants.utils import get_tenant_model, get_tenant_domain_model

logger = logging.getLogger(__name__)

class CustomTenantMiddleware:
    """
    REEMPLAZO COMPLETO de TenantMainMiddleware de django-tenants.
    Detecta el tenant por hostname y configura la conexión a la BD correctamente.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        hostname = request.get_host().split(':')[0].lower()
        
        logger.info(f"🔍 [CustomTenantMiddleware] Hostname: {hostname}")
        
        Domain = get_tenant_domain_model()
        
        try:
            domain = Domain.objects.select_related('tenant').get(domain=hostname)
            tenant = domain.tenant
            
            logger.info(f"✅ Tenant: {tenant.schema_name} (ID: {tenant.id})")
            
            # ESTABLECER el tenant en el request
            request.tenant = tenant
            
            # CONFIGURAR la conexión PostgreSQL al schema correcto
            connection.set_tenant(tenant)
            
            logger.info(f"🗄️ PostgreSQL schema activado: {connection.schema_name}")
            
        except Domain.DoesNotExist:
            logger.warning(f"⚠️ Dominio '{hostname}' no encontrado")
            logger.warning(f"📋 Dominios registrados: {list(Domain.objects.values_list('domain', flat=True))}")
            
            # Si no se encuentra, usar el tenant público
            try:
                tenant = get_tenant_model().objects.get(schema_name='public')
                request.tenant = tenant
                connection.set_tenant(tenant)
                logger.info(f"🏢 Usando tenant público por defecto")
            except Exception as e:
                logger.error(f"❌ Error crítico: {e}")
                raise
        
        # FORZAR el URLConf correcto según el tipo de tenant
        if request.tenant.schema_name == 'public':
            request.urlconf = 'config.urls_public'
            logger.info(f"🌐 URLConf: config.urls_public (Admin Público)")
        else:
            request.urlconf = 'config.urls'
            logger.info(f"🏢 URLConf: config.urls (Admin de Tenant)")
        
        response = self.get_response(request)
        return response
