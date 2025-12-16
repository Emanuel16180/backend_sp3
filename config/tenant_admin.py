# config/tenant_admin.py
# Admin personalizado para los tenants (clínicas individuales)

from django.contrib import admin
from django.contrib.admin import AdminSite

class TenantAdminSite(AdminSite):
    site_header = 'Administración de Clínica'
    site_title = 'Admin Clínica'
    index_title = 'Panel de Administración de la Clínica'

    def has_permission(self, request):
        """
        Solo usuarios autenticados pueden acceder al admin del tenant.
        """
        return request.user.is_active and request.user.is_staff

# Crear instancia del admin site personalizado para tenants
tenant_admin_site = TenantAdminSite(name='tenant_admin')

# NO registramos automáticamente todos los modelos
# En su lugar, cada app debe registrar sus modelos explícitamente