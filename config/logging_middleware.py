"""
Middleware para logging detallado de requests y tenant detection
"""
import logging
import time
from django.db import connection

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """
    Middleware que loguea cada request con información detallada:
    - Método HTTP y path
    - Tenant detectado
    - Schema de base de datos usado
    - Tiempo de respuesta
    - Status code
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Capturar tiempo de inicio
        start_time = time.time()
        
        # Información del request
        method = request.method
        path = request.path
        hostname = request.get_host()
        
        # Log del inicio del request
        logger.info(f"🌐 [{method}] {path}")
        logger.debug(f"   Hostname: {hostname}")
        logger.debug(f"   User-Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')[:50]}")
        
        # Detectar tenant antes del procesamiento
        tenant_name = getattr(request, 'tenant', None)
        if tenant_name:
            logger.debug(f"   🏢 Tenant detectado: {tenant_name.schema_name}")
        
        # Procesar el request
        response = self.get_response(request)
        
        # Capturar schema usado (después del procesamiento)
        schema = connection.schema_name if hasattr(connection, 'schema_name') else 'public'
        
        # Calcular tiempo de respuesta
        duration = time.time() - start_time
        duration_ms = int(duration * 1000)
        
        # Log de la respuesta
        status_emoji = "✅" if 200 <= response.status_code < 300 else "⚠️" if 300 <= response.status_code < 400 else "❌"
        logger.info(f"{status_emoji} [{method}] {path} → {response.status_code} ({duration_ms}ms) [Schema: {schema}]")
        
        # Log adicional si hay errores
        if response.status_code >= 400:
            logger.warning(f"   ⚠️ Error Response: {response.status_code} - Path: {path}")
            
        return response


class TenantDetectionLoggingMiddleware:
    """
    Middleware especializado en loguear la detección de tenants
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        hostname = request.get_host()
        
        # Log antes de la detección del tenant
        logger.debug(f"🔍 [TenantDetection] Hostname: {hostname}")
        
        response = self.get_response(request)
        
        # Log después de la detección
        if hasattr(request, 'tenant'):
            tenant = request.tenant
            logger.debug(f"✅ [TenantDetection] Tenant resuelto: {tenant.schema_name} (ID: {tenant.id})")
        else:
            logger.warning(f"⚠️ [TenantDetection] No se pudo resolver el tenant para hostname: {hostname}")
        
        return response
