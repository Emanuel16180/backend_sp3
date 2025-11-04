# config/urls.py
# Rutas para los tenants (clínicas individuales)

from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from config.admin_site import tenant_admin_site

# Vista raíz para mostrar endpoints disponibles de la clínica
def api_root_tenant(request):
    """Muestra todos los endpoints disponibles para esta clínica"""
    tenant = getattr(request, 'tenant', None)
    tenant_name = tenant.name if tenant else 'Desconocido'
    
    return JsonResponse({
        'message': f'API de {tenant_name}',
        'tenant': tenant.schema_name if tenant else 'public',
        'endpoints': {
            'autenticacion': {
                'login': '/api/auth/login/',
                'logout': '/api/auth/logout/',
                'register': '/api/auth/register/',
                'password_reset': '/api/auth/password-reset/',
            },
            'usuarios': {
                'perfil': '/api/users/profile/',
                'lista': '/api/users/',
            },
            'profesionales': {
                'lista': '/api/professionals/',
                'detalle': '/api/professionals/<id>/',
                'horarios': '/api/professionals/<id>/schedules/',
            },
            'citas': {
                'lista': '/api/appointments/',
                'crear': '/api/appointments/create/',
                'cancelar': '/api/appointments/<id>/cancel/',
            },
            'historia_clinica': {
                'lista': '/api/clinical-history/',
                'notas': '/api/clinical-history/notes/',
                'documentos': '/api/clinical-history/documents/',
            },
            'chat': {
                'mensajes': '/api/chat/messages/',
                'conversaciones': '/api/chat/conversations/',
            },
            'pagos': {
                'checkout': '/api/payments/create-checkout-session/',
                'webhook': '/api/payments/stripe-webhook/',
            },
            'admin': {
                'usuarios': '/api/admin/users/',
                'verificacion': '/api/admin/verify-professionals/',
            },
            'backups': {
                'crear': '/api/backups/create/',
                'lista': '/api/backups/',
            },
            'auditoria': {
                'logs': '/api/auditlog/',
                'filtrar': '/api/auditlog/?user=<id>&action=<action>',
            },
        },
        'admin_panel': '/admin/',
        'documentation': 'https://github.com/tu-repo/docs',
    })

urlpatterns = [
    # Admin ESPECÍFICO para tenants (sin gestión de clínicas)
    path('admin/', tenant_admin_site.urls),

    # Vista raíz del API para mostrar endpoints disponibles
    path('api/', api_root_tenant, name='api-root-tenant'),

    # Todas las rutas de la API para cada clínica
    path('api/auth/', include('apps.authentication.urls')),      # CU-01, CU-02, CU-03, CU-04
    path('api/users/', include('apps.users.urls')),              # CU-05
    path('api/professionals/', include('apps.professionals.urls')), # CU-06, CU-08, CU-09, CU-12
    path('api/appointments/', include('apps.appointments.urls')), # CU-10 ⭐ ESTA ES LA CLAVE
    path('api/clinical-history/', include('apps.clinical_history.urls')), # CU-18, CU-39
    path('api/admin/', include('apps.clinic_admin.urls')),  # CU-30, CU-07 gestión interna de usuarios y verificación
    path('api/payments/', include('apps.payment_system.urls')),  # Sistema de pagos con Stripe
    path('api/chat/', include('apps.chat.urls')),           # Chat por WebSocket
    path('api/backups/', include('apps.backups.urls')),     # Sistema de backups
    path('api/auditlog/', include('apps.auditlog.urls')),   # 👈 NUEVA: Sistema de bitácora
    
    # API browsable (para desarrollo)
    path('api-auth/', include('rest_framework.urls')),
]

# ✅ Servir archivos media SIEMPRE (producción y desarrollo)
from django.views.static import serve
from django.urls import re_path

urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {
        'document_root': settings.MEDIA_ROOT,
    }),
]

# Servir archivos static solo en desarrollo
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)