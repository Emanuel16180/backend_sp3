# config/urls_public.py
# Rutas para el tenant público (admin de tenants)

from django.urls import path, include
from django.http import JsonResponse
from config.admin_site import public_admin_site

# Vista raíz para mostrar endpoints del administrador general
def api_root_public(request):
    """Muestra todos los endpoints disponibles del administrador general"""
    return JsonResponse({
        'message': 'API del Administrador General - Psico Admin',
        'tenant': 'public',
        'description': 'Panel de administración para gestionar múltiples clínicas',
        'endpoints': {
            'autenticacion': {
                'login': '/api/auth/login/',
                'logout': '/api/auth/logout/',
            },
            'gestion_clinicas': {
                'registrar_clinica': '/api/tenants/public/register/',
                'verificar_subdominio': '/api/tenants/public/check-subdomain/',
                'lista_clinicas': '/api/tenants/',
                'detalle_clinica': '/api/tenants/<id>/',
            },
            'pagos_webhooks': {
                'stripe_webhook': '/api/payments/stripe-webhook/',
                'checkout': '/api/payments/create-checkout-session/',
            },
        },
        'admin_panel': '/admin/',
        'features': [
            'Gestión de múltiples clínicas (multi-tenancy)',
            'Registro público de nuevas clínicas',
            'Verificación de subdominios disponibles',
            'Webhooks de pagos globales',
        ],
    })

urlpatterns = [
    # Admin público para gestión de clínicas/tenants
    path('admin/', public_admin_site.urls),
    
    # Vista raíz del API para mostrar endpoints del administrador general
    path('api/', api_root_public, name='api-root-public'),
    
    # ⚠️ IMPORTANTE: Rutas de pagos disponibles en dominio público para webhooks de Stripe
    path('api/payments/', include('apps.payment_system.urls')),  # Sistema de pagos con Stripe
    
    # 🔧 RUTAS ADICIONALES PARA EL TENANT PÚBLICO:
    # Permitir autenticación básica en el tenant público (útil para admin)
    path('api/auth/', include('apps.authentication.urls')),      # Autenticación básica
    
    # API para gestión de clínicas/tenants
    path('api/tenants/', include('apps.tenants.urls')),          # Gestión de clínicas
    
    # API browsable (para desarrollo en tenant público)
    path('api-auth/', include('rest_framework.urls')),
]