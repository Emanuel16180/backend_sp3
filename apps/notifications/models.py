from django.db import models
from django.conf import settings


class PushSubscription(models.Model):
    """
    Guarda las suscripciones de notificaciones push de cada usuario.
    Cada usuario puede tener múltiples dispositivos suscritos.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='push_subscriptions'
    )
    
    # Datos de la suscripción (JSON de la API de Push)
    endpoint = models.URLField(max_length=500, unique=True)
    p256dh = models.CharField(max_length=255, blank=True, null=True)  # Clave pública del cliente (Web Push)
    auth = models.CharField(max_length=255, blank=True, null=True)     # Secret de autenticación (Web Push)
    
    # FCM Token para notificaciones móviles (Firebase)
    fcm_token = models.CharField(max_length=255, blank=True, null=True, db_index=True)
    platform = models.CharField(max_length=20, choices=[('web', 'Web'), ('android', 'Android'), ('ios', 'iOS')], default='web')
    
    # Metadata
    user_agent = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'push_subscriptions'
        verbose_name = 'Suscripción Push'
        verbose_name_plural = 'Suscripciones Push'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['endpoint']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.endpoint[:50]}..."
    
    def to_dict(self):
        """Convierte la suscripción al formato esperado por pywebpush"""
        return {
            "endpoint": self.endpoint,
            "keys": {
                "p256dh": self.p256dh,
                "auth": self.auth
            }
        }


class PushNotification(models.Model):
    """
    Historial de notificaciones enviadas.
    """
    STATUS_CHOICES = (
        ('pending', 'Pendiente'),
        ('sent', 'Enviada'),
        ('failed', 'Fallida'),
    )
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='push_notifications'
    )
    
    title = models.CharField(max_length=255)
    body = models.TextField()
    url = models.CharField(max_length=500, blank=True, null=True)
    icon = models.URLField(blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(blank=True, null=True)
    
    class Meta:
        db_table = 'push_notifications'
        verbose_name = 'Notificación Push'
        verbose_name_plural = 'Notificaciones Push'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.user.email}"
