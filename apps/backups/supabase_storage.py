# apps/backups/supabase_storage.py
import logging
from django.conf import settings
from supabase import create_client, Client
from io import BytesIO

logger = logging.getLogger('apps')
BUCKET_NAME = "backups" # El nombre de tu bucket en Supabase

def get_supabase_client():
    """Inicializa y devuelve el cliente de Supabase."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

def upload_backup_to_supabase(file_content_bytes, file_path_in_bucket):
    """
    Sube un contenido de bytes a Supabase Storage.
    'file_path_in_bucket' debe ser 'nombre_schema/nombre_archivo.sql'
    """
    try:
        supabase: Client = get_supabase_client()
        
        # Determinar content-type
        content_type = 'application/octet-stream'
        if file_path_in_bucket.endswith('.sql'):
            content_type = 'application/sql'
        elif file_path_in_bucket.endswith('.json'):
            content_type = 'application/json'

        supabase.storage.from_(BUCKET_NAME).upload(
            path=file_path_in_bucket,
            file=file_content_bytes,
            file_options={"content-type": content_type, "upsert": "true"}
        )
        
        # Obtener la URL pública (expira en 10 años, básicamente "para siempre")
        public_url = supabase.storage.from_(BUCKET_NAME).get_public_url(file_path_in_bucket)
        
        logger.info(f"Subida a Supabase exitosa: {file_path_in_bucket}")
        return {
            'success': True,
            'path': file_path_in_bucket,
            'url': public_url
        }
    except Exception as e:
        logger.error(f"Error al subir a Supabase: {e}")
        return {'success': False, 'error': str(e)}

def download_backup_from_supabase(file_path_in_bucket):
    """
    Descarga un archivo desde Supabase Storage.
    """
    try:
        supabase: Client = get_supabase_client()
        
        response_bytes = supabase.storage.from_(BUCKET_NAME).download(file_path_in_bucket)
        
        logger.info(f"Descarga de Supabase exitosa: {file_path_in_bucket}")
        return response_bytes
        
    except Exception as e:
        logger.error(f"Error al descargar de Supabase: {e}")
        raise