# apps/backups/cloud_views.py
"""
Vistas para gestión de backups en AWS S3
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status, permissions
from django.http import HttpResponse
from apps.clinic_admin.permissions import IsClinicAdmin
from .s3_storage import S3BackupStorage
import logging

logger = logging.getLogger('apps')


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsClinicAdmin])
def list_cloud_backups(request):
    """
    Lista todos los backups almacenados en S3 para el tenant actual
    """
    try:
        schema_name = request.tenant.schema_name
        s3_storage = S3BackupStorage()
        
        # Listar backups del tenant
        backups = s3_storage.list_backups(folder="backups", schema_name=schema_name)
        
        logger.info(f"Usuario '{request.user.email}' listó {len(backups)} backups de S3")
        
        return Response({
            'count': len(backups),
            'schema': schema_name,
            'backups': backups
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error al listar backups de S3: {e}")
        return Response({
            'error': 'Error al listar backups de S3',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsClinicAdmin])
def download_cloud_backup(request):
    """
    Descarga un backup específico desde S3
    Parámetros:
    - s3_key: Ruta del backup en S3
    """
    try:
        s3_key = request.data.get('s3_key')
        
        if not s3_key:
            return Response({
                'error': 'Debe proporcionar el parámetro s3_key'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar que el backup pertenece al tenant actual
        schema_name = request.tenant.schema_name
        if schema_name not in s3_key:
            logger.warning(f"Usuario '{request.user.email}' intentó acceder a backup de otro tenant")
            return Response({
                'error': 'No tiene permisos para descargar este backup'
            }, status=status.HTTP_403_FORBIDDEN)
        
        s3_storage = S3BackupStorage()
        
        # Descargar el backup
        file_content = s3_storage.download_backup(s3_key)
        filename = s3_key.split('/')[-1]
        
        logger.info(f"Usuario '{request.user.email}' descargó backup: {s3_key}")
        
        # Determinar tipo de contenido por extensión
        if filename.endswith('.sql'):
            content_type = 'application/sql'
        elif filename.endswith('.json'):
            content_type = 'application/json'
        else:
            content_type = 'application/octet-stream'
        
        response = HttpResponse(file_content, content_type=content_type)
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response
        
    except Exception as e:
        logger.error(f"Error al descargar backup de S3: {e}")
        return Response({
            'error': 'Error al descargar backup de S3',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated, IsClinicAdmin])
def delete_cloud_backup(request):
    """
    Elimina un backup específico de S3
    Parámetros:
    - s3_key: Ruta del backup en S3
    """
    try:
        s3_key = request.data.get('s3_key')
        
        if not s3_key:
            return Response({
                'error': 'Debe proporcionar el parámetro s3_key'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar que el backup pertenece al tenant actual
        schema_name = request.tenant.schema_name
        if schema_name not in s3_key:
            logger.warning(f"Usuario '{request.user.email}' intentó eliminar backup de otro tenant")
            return Response({
                'error': 'No tiene permisos para eliminar este backup'
            }, status=status.HTTP_403_FORBIDDEN)
        
        s3_storage = S3BackupStorage()
        
        # Eliminar el backup
        success = s3_storage.delete_backup(s3_key)
        
        if success:
            logger.info(f"Usuario '{request.user.email}' eliminó backup: {s3_key}")
            return Response({
                'message': 'Backup eliminado exitosamente de S3',
                's3_key': s3_key
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'No se pudo eliminar el backup de S3'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        logger.error(f"Error al eliminar backup de S3: {e}")
        return Response({
            'error': 'Error al eliminar backup de S3',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsClinicAdmin])
def get_backup_download_url(request):
    """
    Genera una URL prefirmada para descargar un backup desde S3
    Parámetros:
    - s3_key: Ruta del backup en S3
    - expiration: Tiempo de expiración en segundos (opcional, por defecto 3600 = 1 hora)
    """
    try:
        s3_key = request.data.get('s3_key')
        expiration = request.data.get('expiration', 3600)
        
        if not s3_key:
            return Response({
                'error': 'Debe proporcionar el parámetro s3_key'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Verificar que el backup pertenece al tenant actual
        schema_name = request.tenant.schema_name
        if schema_name not in s3_key:
            logger.warning(f"Usuario '{request.user.email}' intentó generar URL de backup de otro tenant")
            return Response({
                'error': 'No tiene permisos para acceder a este backup'
            }, status=status.HTTP_403_FORBIDDEN)
        
        s3_storage = S3BackupStorage()
        
        # Generar URL prefirmada
        download_url = s3_storage.get_backup_url(s3_key, expiration=expiration)
        
        if download_url:
            logger.info(f"Usuario '{request.user.email}' generó URL de descarga para: {s3_key}")
            return Response({
                'download_url': download_url,
                's3_key': s3_key,
                'expires_in_seconds': expiration,
                'filename': s3_key.split('/')[-1]
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'error': 'No se pudo generar la URL de descarga'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    except Exception as e:
        logger.error(f"Error al generar URL de descarga: {e}")
        return Response({
            'error': 'Error al generar URL de descarga',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
