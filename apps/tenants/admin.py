# apps/tenants/admin.py

from django.contrib import admin
from .models import Clinic, Domain, PublicUser

# Registros simples - el admin personalizado está en config/admin_site.py
# Estos registros son para el admin estándar de Django en los tenants

@admin.register(Clinic)
class ClinicAdmin(admin.ModelAdmin):
    list_display = ('name', 'schema_name', 'created_on')

@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    list_display = ('domain', 'tenant', 'is_primary')