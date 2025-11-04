# apps/auditlog/filters.py
import logging

# Almacenamiento local para el hilo actual (guarda la request de forma segura)
from .local import get_current_request

class RequestInfoFilter(logging.Filter):
    def filter(self, record):
        request = get_current_request()
        if request:
            # Añadir IP y usuario al registro de log
            record.ip_address = request.META.get('REMOTE_ADDR')
            if hasattr(request, 'user') and request.user.is_authenticated:
                record.user = request.user
            else:
                record.user = None
        else:
            record.ip_address = None
            record.user = None
        return True