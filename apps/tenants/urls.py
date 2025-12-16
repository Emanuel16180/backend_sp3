# apps/tenants/urls.py

from django.urls import path
from .views import (
    ClinicListCreateView, 
    ClinicDetailView, 
    global_admin_stats, 
    clinic_detail_stats,
    register_tenant,
    check_subdomain_availability,
    public_clinic_list  # ⭐ NUEVO
)

app_name = 'tenants'

urlpatterns = [
    # ⭐ Endpoints públicos (NO requieren autenticación) - PRIMERO
    path('', public_clinic_list, name='public-clinic-list'),  # ⭐ GET /api/tenants/
    path('public/register/', register_tenant, name='register-tenant'),
    path('public/check-subdomain/', check_subdomain_availability, name='check-subdomain'),
    
    # Endpoints protegidos (requieren autenticación)
    path('clinics/', ClinicListCreateView.as_view(), name='clinic-list-create'),
    path('clinics/<int:pk>/', ClinicDetailView.as_view(), name='clinic-detail'),
    path('admin/stats/', global_admin_stats, name='global-admin-stats'),
    path('clinics/<int:clinic_id>/stats/', clinic_detail_stats, name='clinic-detail-stats'),
]