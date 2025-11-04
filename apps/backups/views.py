# apps/backups/views.py

import subprocess
import datetime
import psycopg2
import json
import os
import tempfile
from django.conf import settings
from django.http import HttpResponse
from django.core.management import call_command
from io import StringIO
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, permission_classes
from apps.clinic_admin.permissions import IsClinicAdmin
from .s3_storage import S3BackupStorage
import logging

# Cambiar para usar el logger de 'apps' que va a la base de datos
logger = logging.getLogger('apps')

class CreateBackupAndDownloadView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsClinicAdmin]

    def post(self, request, *args, **kwargs):
        """
        Crea un backup y lo sube a S3.
        Query params:
        - download=true: descarga el backup localmente
        - cloud_only=true: solo sube a S3, no descarga
        """
        logger.info(f"Usuario '{request.user.email}' solicitó crear un backup.")
        
        # Parámetros de la request
        should_download = request.query_params.get('download', 'false').lower() == 'true'
        cloud_only = request.query_params.get('cloud_only', 'false').lower() == 'true'
        
        try:
            logger.info("Intentando crear backup con pg_dump...")
            backup_data = self._create_backup_with_pg_dump_bytes(request)
            
            # Subir a S3
            s3_storage = S3BackupStorage()
            schema_name = request.tenant.schema_name
            timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S')
            filename = f"backup-sql-{schema_name}-{timestamp}.sql"
            
            result = s3_storage.upload_backup(
                file_content=backup_data,
                filename=filename,
                folder=f"backups/{schema_name}"
            )
            
            if result['success']:
                logger.info(f"Backup subido exitosamente a S3: {result['s3_key']}")
                
                # Si solo queremos subir a la nube, devolver info
                if cloud_only or not should_download:
                    return Response({
                        'message': 'Backup creado y subido a S3 exitosamente',
                        'backup_info': {
                            'filename': result['filename'],
                            's3_key': result['s3_key'],
                            'size': result['size'],
                            'bucket': result['bucket'],
                            'url': result['url']
                        }
                    }, status=status.HTTP_200_OK)
                
                # Si queremos descargar, devolver el archivo
                response = HttpResponse(backup_data, content_type='application/sql')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                response['X-S3-Key'] = result['s3_key']  # Header personalizado con la ubicación en S3
                return response
            else:
                logger.error(f"Error al subir backup a S3: {result.get('error')}")
                return Response({
                    'error': 'Error al subir backup a S3',
                    'details': result.get('error')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except Exception as e:
            logger.warning(f"pg_dump falló. Usando fallback de Django. Error: {e}")
            return self._create_backup_with_django(request)

    def _create_backup_with_pg_dump_bytes(self, request):
        """Genera un backup en formato .sql usando pg_dump y devuelve bytes."""
        schema_name = request.tenant.schema_name
        db_settings = settings.DATABASES['default']

        command = [
            'pg_dump', '--dbname', db_settings['NAME'], '--host', '127.0.0.1',
            '--port', str(db_settings['PORT']), '--username', db_settings['USER'],
            '--schema', schema_name, '--format', 'p', '--inserts', '--no-owner', '--no-privileges'
        ]
        env = {'PGPASSWORD': db_settings['PASSWORD']}

        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        stdout, stderr = process.communicate()

        if process.returncode != 0:
            logger.error(f"Error en pg_dump: {stderr.decode()}")
            raise subprocess.CalledProcessError(process.returncode, command, stderr=stderr)

        logger.info(f"Backup SQL creado exitosamente para el schema '{schema_name}'.")
        return stdout

    def _create_backup_with_django(self, request):
        """Método de fallback que usa 'dumpdata' de Django para crear un backup .json."""
        schema_name = request.tenant.schema_name
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S')
        filename = f"backup-json-{schema_name}-{timestamp}.json"

        logger.info(f"Creando backup JSON para {schema_name} usando Django dumpdata.")

        buffer = StringIO()
        tenant_apps = ['users', 'professionals', 'appointments', 'chat', 'clinical_history', 'payment_system']
        call_command('dumpdata', *tenant_apps, format='json', indent=2, stdout=buffer)
        buffer.seek(0)

        logger.info(f"Backup JSON creado exitosamente para el schema '{schema_name}'.")

        response = HttpResponse(buffer.getvalue(), content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{filename}"'
        return response


class RestoreBackupFromFileView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsClinicAdmin]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, *args, **kwargs):
        if 'backup_file' not in request.FILES:
            return Response({'error': 'No se proporcionó ningún archivo.'}, status=status.HTTP_400_BAD_REQUEST)

        backup_file = request.FILES['backup_file']
        
        # 🔽 EJEMPLO DE REGISTRO
        logger.info(f"Usuario '{request.user.email}' inició una restauración con el archivo '{backup_file.name}'.")
        
        # --- CORRECCIÓN ADICIONAL: Prohibir restaurar el schema 'public' ---
        if request.tenant.schema_name == 'public':
            logger.warning(f"Usuario '{request.user.email}' intentó restaurar el esquema público (prohibido).")
            return Response({'error': 'No está permitido restaurar el esquema público.'}, status=status.HTTP_403_FORBIDDEN)

        if backup_file.name.endswith('.sql'):
            return self._restore_sql_backup(request, backup_file)
        elif backup_file.name.endswith('.json'):
            return self._restore_json_backup(request, backup_file)
        else:
            return Response({'error': 'Formato de archivo no soportado. Use .sql o .json.'}, status=status.HTTP_400_BAD_REQUEST)

    def _restore_sql_backup(self, request, backup_file):
        schema_name = request.tenant.schema_name
        db_settings = settings.DATABASES['default']
        env = {'PGPASSWORD': db_settings['PASSWORD']}
        
        logger.info(f"Iniciando restauración SQL para el schema '{schema_name}'.")
        
        try:
            # --- CORRECCIÓN 1: Usar '127.0.0.1' en la conexión ---
            conn = psycopg2.connect(
                dbname=db_settings['NAME'], user=db_settings['USER'],
                password=db_settings['PASSWORD'], host='127.0.0.1', port=db_settings['PORT']
            )
            conn.autocommit = True
            with conn.cursor() as cursor:
                cursor.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE;')
                cursor.execute(f'CREATE SCHEMA "{schema_name}";')
                cursor.execute(f'GRANT ALL ON SCHEMA "{schema_name}" TO "{db_settings["USER"]}";')
            conn.close()

            logger.info(f"Schema '{schema_name}' recreado exitosamente.")

            # --- CORRECCIÓN 1: Usar '127.0.0.1' para psql ---
            restore_command = [
                'psql', '--dbname', db_settings['NAME'], '--host', '127.0.0.1',
                '--port', str(db_settings['PORT']), '--username', db_settings['USER'],
                '--single-transaction'
            ]
            process = subprocess.run(restore_command, input=backup_file.read(), capture_output=True, check=True, env=env)
            
            # 🔽 EJEMPLO DE REGISTRO DE ÉXITO
            logger.info(f"Restauración SQL completada para el schema '{request.tenant.schema_name}'.")
            return Response({'status': 'Restauración desde SQL completada.'}, status=status.HTTP_200_OK)
        except subprocess.CalledProcessError as e:
            # 🔽 EJEMPLO DE REGISTRO DE ERROR
            logger.error(f"Error en subprocess de restauración SQL: {e.stderr.decode()}")
            return Response({'error': f"Error en la restauración SQL: {e.stderr.decode()}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            # 🔽 EJEMPLO DE REGISTRO DE ERROR CRÍTICO
            logger.error(f"FALLO CRÍTICO en la restauración SQL: {e}", exc_info=True)
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _restore_json_backup(self, request, backup_file):
        """Restaura desde un archivo JSON usando archivos temporales."""
        temp_file_path = None
        
        logger.info(f"Iniciando restauración JSON para el schema '{request.tenant.schema_name}'.")
        
        try:
            with tempfile.NamedTemporaryFile(delete=False, mode='w+', suffix='.json', encoding='utf-8') as temp_file:
                temp_file.write(backup_file.read().decode('utf-8'))
                temp_file_path = temp_file.name
            
            logger.info("Limpiando datos del tenant de forma segura (preservando admins).")
            self._clear_tenant_data_safe()
            
            logger.info(f"Cargando datos desde archivo temporal: {temp_file_path}")
            call_command('loaddata', temp_file_path)
            
            logger.info(f"Restauración JSON completada para el schema '{request.tenant.schema_name}'.")
            return Response({'status': 'Restauración desde JSON completada.'}, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error en restauración JSON: {str(e)}")
            return Response({'error': f"Error en la restauración JSON: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                    logger.info(f"Archivo temporal eliminado: {temp_file_path}")
                except Exception as e:
                    logger.warning(f"No se pudo eliminar archivo temporal {temp_file_path}: {e}")

    def _clear_tenant_data_safe(self):
        """Borra solo los datos del tenant actual, preservando los administradores."""
        try:
            from apps.users.models import CustomUser
            from apps.appointments.models import Appointment
            from apps.chat.models import ChatMessage
            from apps.professionals.models import ProfessionalProfile
            from apps.users.models import PatientProfile
            
            logger.info("Iniciando limpieza de datos del tenant (preservando admins)...")
            
            ChatMessage.objects.all().delete()
            Appointment.objects.all().delete()
            PatientProfile.objects.all().delete()
            ProfessionalProfile.objects.all().delete()
            
            # --- CORRECCIÓN 2: No eliminar usuarios 'admin' ---
            CustomUser.objects.filter(user_type__in=['patient', 'professional']).delete()
            logger.info("Usuarios de tipo 'paciente' y 'profesional' eliminados.")
            
            logger.info("Limpieza de datos del tenant completada exitosamente.")
            
        except Exception as e:
            logger.error(f"Error en limpieza segura de datos: {e}")
            raise

# =========================================================================
#  NUEVAS VISTAS PARA GESTI�N DE BACKUPS EN S3
# =========================================================================
