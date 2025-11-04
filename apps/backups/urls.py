# apps/backups/urls.py

from django.urls import path
from .views import CreateBackupAndDownloadView, RestoreBackupFromFileView
from .cloud_views import (
    list_cloud_backups,
    download_cloud_backup,
    delete_cloud_backup,
    get_backup_download_url
)

urlpatterns = [
    # Rutas originales (local + S3)
    path('create/', CreateBackupAndDownloadView.as_view(), name='create-backup'),
    path('restore/', RestoreBackupFromFileView.as_view(), name='restore-backup'),
    
    # Nuevas rutas para gestión de backups en S3
    path('cloud/list/', list_cloud_backups, name='list-cloud-backups'),
    path('cloud/download/', download_cloud_backup, name='download-cloud-backup'),
    path('cloud/delete/', delete_cloud_backup, name='delete-cloud-backup'),
    path('cloud/get-url/', get_backup_download_url, name='get-backup-url'),
]
