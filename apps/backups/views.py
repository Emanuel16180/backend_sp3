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
from rest_framework import status, permissions, generics
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import api_view, permission_classes
from apps.clinic_admin.permissions import IsClinicAdmin
from .s3_storage import S3BackupStorage
import logging
from .models import BackupRecord
from .serializers import BackupRecordSerializer
from .supabase_storage import upload_backup_to_supabase, download_backup_from_supabase

# Cambiar para usar el logger de 'apps' que va a la base de datos
logger = logging.getLogger('apps')

class CreateBackupView(APIView):
    """
    Crea un backup (SQL o JSON), lo sube a Supabase,
    y crea un registro en la base de datos.
    """
    permission_classes = [permissions.IsAuthenticated, IsClinicAdmin]

    def post(self, request, *args, **kwargs):
        # Parámetros
        should_download = request.query_params.get('download', 'false').lower() == 'true'
        schema_name = request.tenant.schema_name
        timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S')
        
        backup_data_bytes = None
        file_type = ""

        # --- 1. Intentar pg_dump (Backup SQL) ---
        try:
            logger.info("Intentando crear backup con pg_dump...")
            backup_data_bytes = self._create_pg_dump_bytes(schema_name)
            file_name = f"backup-sql-{schema_name}-{timestamp}.sql"
            file_type = "sql"
        
        except Exception as e:
            logger.warning(f"pg_dump falló. Usando fallback de Django (JSON). Error: {e}")
            
            # --- 2. Fallback a Django (Backup JSON) ---
            try:
                backup_data_bytes = self._create_django_dump_bytes()
                file_name = f"backup-json-{schema_name}-{timestamp}.json"
                file_type = "json"
            except Exception as e_json:
                logger.error(f"Fallback de JSON también falló: {e_json}")
                return Response({'error': 'No se pudo generar el backup (falló SQL y JSON)'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if not backup_data_bytes:
             return Response({'error': 'No se pudo generar el backup (datos vacíos)'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # --- 3. Subir a Supabase ---
        file_path_in_bucket = f"{schema_name}/{file_name}"
        upload_result = upload_backup_to_supabase(backup_data_bytes, file_path_in_bucket)

        if not upload_result['success']:
            return Response({'error': 'Fallo al subir a Supabase', 'details': upload_result.get('error')}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # --- 4. Crear registro en la BD ---
        record = BackupRecord.objects.create(
            file_name=file_name,
            file_path=upload_result['path'],
            file_size=len(backup_data_bytes),
            backup_type='manual',
            created_by=request.user
        )

        logger.info(f"Backup manual creado y registrado (ID: {record.id})")

        # --- 5. Decidir si descargar o solo mostrar info ---
        if should_download:
            content_type = 'application/sql' if file_type == 'sql' else 'application/json'
            response = HttpResponse(backup_data_bytes, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'
            return response
        else:
            return Response({
                'message': 'Backup creado y subido a Supabase exitosamente',
                'backup_info': BackupRecordSerializer(record).data
            }, status=status.HTTP_201_CREATED)


    def _create_pg_dump_bytes(self, schema_name):
        """Genera un backup en formato .sql usando pg_dump y devuelve bytes."""
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
            raise subprocess.CalledProcessError(process.returncode, command, stderr=stderr)
        return stdout

    def _create_django_dump_bytes(self):
        """Método de fallback que usa 'dumpdata' de Django y devuelve bytes."""
        buffer = StringIO()
        tenant_apps = ['users', 'professionals', 'appointments', 'chat', 'clinical_history', 'payment_system']
        call_command('dumpdata', *tenant_apps, format='json', indent=2, stdout=buffer)
        return buffer.getvalue().encode('utf-8')


class BackupHistoryListView(generics.ListAPIView):
    """
    NUEVA VISTA: Muestra el registro de todos los backups
    creados para esta clínica.
    """
    serializer_class = BackupRecordSerializer
    permission_classes = [permissions.IsAuthenticated, IsClinicAdmin]

    def get_queryset(self):
        # Devuelve todos los records del tenant actual
        return BackupRecord.objects.all()


class DownloadBackupView(generics.RetrieveAPIView):
    """
    NUEVA VISTA: Descarga un backup específico desde
    Supabase usando su ID de registro.
    """
    queryset = BackupRecord.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsClinicAdmin]

    def retrieve(self, request, *args, **kwargs):
        record = self.get_object()
        
        try:
            file_content_bytes = download_backup_from_supabase(record.file_path)
            
            # Determinar content-type
            content_type = 'application/octet-stream'
            if record.file_name.endswith('.sql'):
                content_type = 'application/sql'
            elif record.file_name.endswith('.json'):
                content_type = 'application/json'

            response = HttpResponse(file_content_bytes, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{record.file_name}"'
            return response

        except Exception as e:
            return Response({'error': f'No se pudo descargar el archivo: {e}'}, status=status.HTTP_404_NOT_FOUND)

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
