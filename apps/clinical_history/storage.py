# apps/clinical_history/storage.py

from django.core.files.storage import Storage
from apps.backups.s3_storage import S3BackupStorage
from django.conf import settings
import logging
import os

logger = logging.getLogger('apps')

class ClinicalDocumentS3Storage(Storage):
    """
    Storage personalizado para documentos clínicos en S3
    """
    
    def __init__(self):
        self.s3_storage = S3BackupStorage()
        self.base_folder = "clinical_documents"
    
    def _save(self, name, content):
        """
        Guarda el archivo en S3
        
        Args:
            name: Ruta del archivo (ej: clinical_documents/2025/10/21/doc.pdf)
            content: File object
        
        Returns:
            str: Nombre del archivo guardado en S3
        """
        try:
            # Leer contenido del archivo
            file_content = content.read()
            
            # Subir a S3
            result = self.s3_storage.upload_file(
                file_content=file_content,
                filename=name,
                folder="media",  # Todo va en /media/
                content_type=self._guess_content_type(name)
            )
            
            if result['success']:
                logger.info(f"✅ [S3Storage] Documento guardado: {result['s3_key']}")
                return result['s3_key']  # Devuelve la key completa
            else:
                logger.error(f"❌ [S3Storage] Error al guardar: {result.get('error')}")
                raise Exception(result.get('error', 'Error desconocido'))
                
        except Exception as e:
            logger.error(f"❌ [S3Storage] Excepción al guardar archivo: {e}")
            raise
    
    def _open(self, name, mode='rb'):
        """
        Abre el archivo desde S3
        
        Args:
            name: Ruta del archivo en S3
            mode: Modo de apertura
        
        Returns:
            File-like object con el contenido
        """
        try:
            from io import BytesIO
            
            # Descargar desde S3
            content = self.s3_storage.download_file(name)
            
            logger.info(f"✅ [S3Storage] Archivo abierto: {name}")
            return BytesIO(content)
            
        except Exception as e:
            logger.error(f"❌ [S3Storage] Error al abrir archivo: {e}")
            raise
    
    def exists(self, name):
        """
        Verifica si el archivo existe en S3
        
        Args:
            name: Ruta del archivo
        
        Returns:
            bool: True si existe
        """
        try:
            self.s3_storage.s3_client.head_object(
                Bucket=self.s3_storage.bucket_name,
                Key=name
            )
            return True
        except:
            return False
    
    def url(self, name):
        """
        Genera URL para acceder al archivo
        
        Args:
            name: Ruta del archivo en S3
        
        Returns:
            str: URL del archivo
        """
        # Si está en modo desarrollo local, devolver URL local
        if settings.DEBUG and not settings.USE_S3_STORAGE:
            return f"/media/{name}"
        
        # En producción, generar URL prefirmada de S3
        return self.s3_storage.get_backup_url(name, expiration=3600)  # 1 hora
    
    def size(self, name):
        """
        Obtiene el tamaño del archivo
        
        Args:
            name: Ruta del archivo
        
        Returns:
            int: Tamaño en bytes
        """
        try:
            response = self.s3_storage.s3_client.head_object(
                Bucket=self.s3_storage.bucket_name,
                Key=name
            )
            return response['ContentLength']
        except:
            return 0
    
    def delete(self, name):
        """
        Elimina el archivo de S3
        
        Args:
            name: Ruta del archivo
        """
        try:
            self.s3_storage.delete_backup(name)
            logger.info(f"✅ [S3Storage] Archivo eliminado: {name}")
        except Exception as e:
            logger.error(f"❌ [S3Storage] Error al eliminar: {e}")
            raise
    
    def _guess_content_type(self, filename):
        """
        Adivina el content type basado en la extensión
        
        Args:
            filename: Nombre del archivo
        
        Returns:
            str: Content type
        """
        ext = os.path.splitext(filename)[1].lower()
        
        content_types = {
            '.pdf': 'application/pdf',
            '.doc': 'application/msword',
            '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            '.txt': 'text/plain',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif'
        }
        
        return content_types.get(ext, 'application/octet-stream')
