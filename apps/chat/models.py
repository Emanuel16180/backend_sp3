# apps/chat/models.py
from django.db import models
from django.conf import settings  # ← Importar settings

class ChatMessage(models.Model):
    appointment_id = models.IntegerField()
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # ← Cambiar aquí
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.sender.username}: {self.message[:50]}"