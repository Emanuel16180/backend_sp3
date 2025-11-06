# apps/backups/urls.py

from django.urls import path
from .views import (
    CreateBackupView, 
    RestoreBackupFromFileView,
    BackupHistoryListView,
    DownloadBackupView
)

urlpatterns = [
    # Ruta original para crear (manual) y descargar
    path('create/', CreateBackupView.as_view(), name='create-backup'),
    
    # Ruta original para restaurar
    path('restore/', RestoreBackupFromFileView.as_view(), name='restore-backup'),
    
    # --- 👇 NUEVAS RUTAS PARA EL REGISTRO 👇 ---
    
    # (GET) Listar todos los backups registrados en la BD
    path('history/', BackupHistoryListView.as_view(), name='list-backup-history'),
    
    # (GET) Descargar un backup específico por su ID
    path('history/<int:pk>/download/', DownloadBackupView.as_view(), name='download-backup-history'),
]