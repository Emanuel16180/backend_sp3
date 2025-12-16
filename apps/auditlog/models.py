# apps/auditlog/models.py
from django.db import models
from django.conf import settings

class LogEntry(models.Model):
    LEVEL_CHOICES = (
        ('INFO', 'Info'),
        ('WARNING', 'Warning'),
        ('ERROR', 'Error'),
        ('CRITICAL', 'Critical'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="Usuario",
        related_name="audit_logs"
    )
    ip_address = models.GenericIPAddressField(
        verbose_name="Dirección IP",
        null=True,
        blank=True
    )
    level = models.CharField(
        max_length=10,
        choices=LEVEL_CHOICES,
        default='INFO',
        verbose_name="Nivel"
    )
    action = models.TextField(verbose_name="Acción o Mensaje")
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name="Marca de Tiempo")
    details = models.JSONField(default=dict, blank=True, verbose_name="Detalles Adicionales")

    class Meta:
        verbose_name = "Registro de Bitácora"
        verbose_name_plural = "Registros de Bitácora"
        ordering = ['-timestamp']
        db_table = 'audit_log_entries'

    def __str__(self):
        return f'[{self.timestamp.strftime("%Y-%m-%d %H:%M")}] [{self.level}] {self.action}'
