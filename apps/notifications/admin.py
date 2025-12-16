from django.contrib import admin
from .models import PushSubscription, PushNotification


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'endpoint_short', 'is_active', 'created_at', 'last_used']
    list_filter = ['is_active', 'created_at']
    search_fields = ['user__email', 'endpoint']
    readonly_fields = ['endpoint', 'p256dh', 'auth', 'user_agent', 'created_at', 'last_used']
    
    def endpoint_short(self, obj):
        return obj.endpoint[:50] + '...' if len(obj.endpoint) > 50 else obj.endpoint
    endpoint_short.short_description = 'Endpoint'


@admin.register(PushNotification)
class PushNotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'user', 'status', 'created_at', 'sent_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'body', 'user__email']
    readonly_fields = ['user', 'title', 'body', 'url', 'icon', 'status', 'error_message', 'created_at', 'sent_at']
    
    fieldsets = (
        ('Información', {
            'fields': ('user', 'title', 'body', 'url', 'icon')
        }),
        ('Estado', {
            'fields': ('status', 'error_message', 'created_at', 'sent_at')
        }),
    )
