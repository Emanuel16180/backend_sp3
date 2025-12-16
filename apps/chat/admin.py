from django.contrib import admin
from .models import ChatMessage

class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'appointment_id', 'message_preview', 'timestamp')
    list_filter = ('timestamp', 'appointment_id')
    search_fields = ('sender__first_name', 'sender__last_name', 'message')
    readonly_fields = ('timestamp',)
    
    def message_preview(self, obj):
        return obj.message[:50] + "..." if len(obj.message) > 50 else obj.message
    message_preview.short_description = 'Mensaje'

# NO registrar en el admin por defecto - se registran en admin sites específicos
# admin.site.register(ChatMessage, ChatMessageAdmin)

# Registrar también en el tenant admin
from config.tenant_admin import tenant_admin_site
tenant_admin_site.register(ChatMessage, ChatMessageAdmin)
