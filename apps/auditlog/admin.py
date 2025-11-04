# apps/auditlog/admin.py
from django.contrib import admin
from .models import LogEntry
from config.admin_site import tenant_admin_site

class LogEntryAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'user', 'ip_address', 'level', 'action')
    list_filter = ('level', 'timestamp')
    search_fields = ('user__email', 'action', 'ip_address')
    readonly_fields = [f.name for f in LogEntry._meta.fields]  # Hace todos los campos de solo lectura

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

# Registrar en el admin de las clínicas
tenant_admin_site.register(LogEntry, LogEntryAdmin)
