from django.conf import settings
from django.urls import set_urlconf
from django.db import connection


class TenantURLConfMiddleware:
    """
    Middleware para forzar el URLconf correcto según el tenant.
    Se ejecuta DESPUÉS de TenantMainMiddleware.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Verificar el schema actual
        if hasattr(connection, 'schema_name'):
            if connection.schema_name != 'public':
                # Estamos en un tenant, forzar URLconf de tenant
                set_urlconf(settings.TENANT_URLCONF)
                request.urlconf = settings.TENANT_URLCONF
            else:
                # Estamos en público, usar URLconf público
                set_urlconf(settings.ROOT_URLCONF)
                request.urlconf = settings.ROOT_URLCONF

        response = self.get_response(request)
        return response