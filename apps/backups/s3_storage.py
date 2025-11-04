# apps/backups/s3_storage.py

import boto3
from botocore.exceptions import ClientError, NoCredentialsError
from django.conf import settings
import logging

logger = logging.getLogger('apps')

class S3BackupStorage:
    """Clase para gestionar backups Y ARCHIVOS MULTIMEDIA en AWS S3"""
    
    def __init__(self):
        self.bucket_name = settings.AWS_STORAGE_BUCKET_NAME
        self.region = settings.AWS_S3_REGION_NAME
        
        # Crear cliente S3
        try:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=self.region
            )
            logger.info(f"✅ Cliente S3 inicializado correctamente para bucket: {self.bucket_name}")
        except NoCredentialsError:
            logger.error("❌ Credenciales de AWS no encontradas")
            raise
        except Exception as e:
            logger.error(f"❌ Error al inicializar cliente S3: {e}")
            raise
    
    def upload_file(self, file_content, filename, folder="media", content_type=None):
        """
        Sube un archivo a S3 (genérico para backups Y documentos clínicos)
        
        Args:
            file_content: Contenido del archivo (bytes o file-like object)
            filename: Nombre del archivo
            folder: Carpeta dentro del bucket (por defecto 'media')
            content_type: MIME type del archivo (auto-detectar si es None)
        
        Returns:
            dict: Información del archivo subido
        """
        try:
            # Construir la ruta completa en S3
            s3_key = f"{folder}/{filename}"
            
            # Detectar content type si no se proporciona
            if content_type is None:
                if filename.endswith('.pdf'):
                    content_type = 'application/pdf'
                elif filename.endswith('.png'):
                    content_type = 'image/png'
                elif filename.endswith('.jpg') or filename.endswith('.jpeg'):
                    content_type = 'image/jpeg'
                else:
                    content_type = 'application/octet-stream'
            
            # Subir el archivo
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                ContentType=content_type,
                ServerSideEncryption='AES256',  # Encriptar en servidor
                Metadata={
                    'uploaded_by': 'psico-admin-system',
                    'file_type': folder
                }
            )
            
            # Construir URL del archivo
            file_url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            
            logger.info(f"✅ Archivo subido exitosamente a S3: {s3_key}")
            
            return {
                'success': True,
                'filename': filename,
                's3_key': s3_key,
                'url': file_url,
                'bucket': self.bucket_name,
                'size': len(file_content) if hasattr(file_content, '__len__') else 0
            }
            
        except ClientError as e:
            error_message = f"Error al subir archivo a S3: {e}"
            logger.error(f"❌ {error_message}")
            return {
                'success': False,
                'error': error_message
            }
        except Exception as e:
            error_message = f"Error inesperado al subir archivo: {e}"
            logger.error(f"❌ {error_message}")
            return {
                'success': False,
                'error': error_message
            }
    
    def upload_backup(self, file_content, filename, folder="backups"):
        """
        Sube un backup a S3 (mantiene compatibilidad con código existente)
        
        Args:
            file_content: Contenido del archivo (bytes)
            filename: Nombre del archivo
            folder: Carpeta dentro del bucket (por defecto 'backups')
        
        Returns:
            dict: Información del archivo subido
        """
        return self.upload_file(file_content, filename, folder, content_type='application/octet-stream')
    
    def download_file(self, s3_key):
        """
        Descarga un archivo desde S3 (genérico)
        
        Args:
            s3_key: Ruta del archivo en S3
        
        Returns:
            bytes: Contenido del archivo
        """
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            file_content = response['Body'].read()
            logger.info(f"✅ Archivo descargado exitosamente desde S3: {s3_key}")
            
            return file_content
            
        except ClientError as e:
            logger.error(f"❌ Error al descargar archivo desde S3: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Error inesperado al descargar archivo: {e}")
            raise
    
    def download_backup(self, s3_key):
        """Alias para compatibilidad con código existente"""
        return self.download_file(s3_key)
    
    def list_backups(self, folder="backups", schema_name=None):
        """
        Lista todos los backups en S3
        
        Args:
            folder: Carpeta a listar (por defecto 'backups')
            schema_name: Filtrar por schema (opcional)
        
        Returns:
            list: Lista de backups con su información
        """
        try:
            prefix = f"{folder}/"
            if schema_name:
                prefix = f"{folder}/backup-{schema_name}"
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            backups = []
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    # Obtener metadata del archivo
                    try:
                        head_response = self.s3_client.head_object(
                            Bucket=self.bucket_name,
                            Key=obj['Key']
                        )
                        
                        backups.append({
                            'filename': obj['Key'].split('/')[-1],
                            's3_key': obj['Key'],
                            'size': obj['Size'],
                            'last_modified': obj['LastModified'].isoformat(),
                            'storage_class': obj.get('StorageClass', 'STANDARD'),
                            'url': f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{obj['Key']}"
                        })
                    except Exception as e:
                        logger.warning(f"No se pudo obtener metadata de {obj['Key']}: {e}")
                        continue
            
            logger.info(f"Se encontraron {len(backups)} backups en S3")
            return backups
            
        except ClientError as e:
            logger.error(f"Error al listar backups en S3: {e}")
            return []
        except Exception as e:
            logger.error(f"Error inesperado al listar backups: {e}")
            return []
    
    def delete_backup(self, s3_key):
        """
        Elimina un backup de S3
        
        Args:
            s3_key: Ruta del archivo en S3
        
        Returns:
            bool: True si se eliminó correctamente
        """
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            logger.info(f"Backup eliminado exitosamente de S3: {s3_key}")
            return True
            
        except ClientError as e:
            logger.error(f"Error al eliminar backup de S3: {e}")
            return False
        except Exception as e:
            logger.error(f"Error inesperado al eliminar backup: {e}")
            return False
    
    def get_backup_url(self, s3_key, expiration=3600):
        """
        Genera una URL prefirmada para descargar un backup
        
        Args:
            s3_key: Ruta del archivo en S3
            expiration: Tiempo de expiración en segundos (por defecto 1 hora)
        
        Returns:
            str: URL prefirmada
        """
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': self.bucket_name,
                    'Key': s3_key
                },
                ExpiresIn=expiration
            )
            
            logger.info(f"URL prefirmada generada para {s3_key}")
            return url
            
        except ClientError as e:
            logger.error(f"Error al generar URL prefirmada: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inesperado al generar URL: {e}")
            return None
