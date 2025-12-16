# apps/backups/models.py
from django.db import models
from django.conf import settings

class BackupRecord(models.Model):
    """
    Un registro de cada backup (manual o automático)
    que se ha subido a la nube.
    """
    BACKUP_TYPES = (
        ('manual', 'Manual'),
        ('automatic', 'Automático'),
    )
    
    file_name = models.CharField(max_length=255)
    file_path = models.TextField(help_text="Ruta completa en el bucket de Supabase")
    file_size = models.BigIntegerField(help_text="Tamaño en bytes")
    backup_type = models.CharField(max_length=10, choices=BACKUP_TYPES, default='manual')
    
    # Nulo si es automático
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, 
        blank=True
    ) 
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Registro de Backup"
        verbose_name_plural = "Registros de Backups"

    def __str__(self):
        return f"{self.file_name} ({self.backup_type})"