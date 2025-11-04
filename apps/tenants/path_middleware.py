# apps/tenants/path_middleware.py
from django.http import Http404
from django_tenants.middleware.main import TenantMainMiddleware
from apps.tenants.models import Clinic

class TenantPathMiddleware(TenantMainMiddleware):
    """
    Middleware que detecta el tenant por la ruta en lugar del dominio.
    
    URLs soportadas:
    - /bienestar/... → usa schema 'bienestar'
    - /mindcare/... → usa schema 'mindcare'
    - Cualquier otra ruta → usa schema 'public'
    """
    
    def get_tenant(self, domain_model, hostname, request):
        """
        Detecta el tenant basándose en la ruta de la URL.
        """
        path = request.path_info
        
        # Detectar tenant por el primer segmento de la ruta
        if path.startswith('/bienestar/'):
            schema_name = 'bienestar'
        elif path.startswith('/mindcare/'):
            schema_name = 'mindcare'
        else:
            # Para cualquier otra ruta, usar el esquema público
            schema_name = 'public'
        
        try:
            tenant = Clinic.objects.get(schema_name=schema_name)
            
            # Remover el prefijo del tenant de la ruta para que Django procese correctamente
            if schema_name != 'public':
                request.path_info = path.replace(f'/{schema_name}', '', 1)
                if not request.path_info:
                    request.path_info = '/'
            
            return tenant
        except Clinic.DoesNotExist:
            raise Http404(f"No existe el tenant: {schema_name}")
