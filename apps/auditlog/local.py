# apps/auditlog/local.py
import threading

_request_storage = threading.local()

def get_current_request():
    return getattr(_request_storage, 'request', None)

class RequestLocalStorageMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _request_storage.request = request
        response = self.get_response(request)
        # Limpiar después de que la petición termine
        if hasattr(_request_storage, 'request'):
            del _request_storage.request
        return response