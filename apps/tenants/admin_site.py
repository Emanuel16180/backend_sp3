# apps/tenants/admin_site.py

from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.auth.admin import UserAdmin
from .models import Clinic, Domain, PublicUser

class PublicAdminSite(AdminSite):
    """
    Admin site personalizado para el esquema público.
    Solo gestiona clínicas y dominios, sin logs ni acciones.
    """
    site_header = 'Gestión de Clínicas - Psico Admin'
    site_title = 'Psico Admin'
    index_title = 'Panel de Administración de Clínicas'
    
    def get_app_list(self, request, app_label=None):
        """
        Personalizar la lista de apps mostradas
        """
        app_list = super().get_app_list(request, app_label)
        
        # Filtrar solo las apps que queremos mostrar
        filtered_apps = []
        for app in app_list:
            if app['app_label'] in ['tenants']:
                filtered_apps.append(app)
        
        return filtered_apps

# Crear instancia del admin site personalizado
public_admin = PublicAdminSite(name='public_admin')

# Registrar modelos en el admin personalizado
@admin.register(Clinic, site=public_admin)
class ClinicAdmin(admin.ModelAdmin):
    list_display = ('name', 'schema_name', 'created_on')
    search_fields = ('name', 'schema_name')
    readonly_fields = ('created_on',)

@admin.register(Domain, site=public_admin)
class DomainAdmin(admin.ModelAdmin):
    list_display = ('domain', 'tenant', 'is_primary')
    list_filter = ('is_primary',)
    search_fields = ('domain',)

@admin.register(PublicUser, site=public_admin)
class PublicUserAdmin(UserAdmin):
    """Admin para usuarios del esquema público"""
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active', 'date_joined')
    ordering = ('email',)
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'last_name')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Fechas Importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'is_staff', 'is_active')}
        ),
    )