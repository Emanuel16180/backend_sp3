# apps/clinic_admin/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserManagementViewSet, PaymentReportView

# Creamos un router para los ViewSets
router = DefaultRouter()
router.register(r'users', UserManagementViewSet, basename='clinic-users')

# --- 👇 ¡CAMBIO CLAVE! Registramos el reporte como un ViewSet 👇 ---
router.register(r'reports/payments', PaymentReportView, basename='payment-report')

urlpatterns = [
    # El router ahora maneja todas las URLs
    path('', include(router.urls)),
]