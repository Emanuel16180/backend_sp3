# apps/backups/management/commands/run_scheduled_backups.py

import logging
from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context
from apps.tenants.models import Clinic
from apps.backups.models import BackupRecord
from apps.backups.supabase_storage import upload_backup_to_supabase
from apps.backups.views import CreateBackupView
from django.utils import timezone
import datetime

logger = logging.getLogger('apps')

class Command(BaseCommand):
    help = 'Ejecuta los backups automáticos o programados.'

    def handle(self, *args, **options):
        self.stdout.write("⏳ Verificando backups programados...")
        
        # Obtener todas las clínicas
        clinics = Clinic.objects.exclude(schema_name='public')
        
        # Obtener la hora actual con zona horaria
        now = timezone.now()
        
        for clinic in clinics:
            schedule = clinic.backup_schedule
            run_backup = False
            
            if schedule == 'disabled':
                continue

            # --- LÓGICA DE PROGRAMACIÓN EXACTA ---
            if schedule == 'scheduled':
                if clinic.next_scheduled_backup and clinic.next_scheduled_backup <= now:
                    # Si hay fecha programada y YA PASÓ (o es ahora), ejecutamos
                    run_backup = True
                    self.stdout.write(f"⏰ Ejecutando backup programado para {clinic.name} (Era para: {clinic.next_scheduled_backup})")
                else:
                    # Aún no es la hora
                    continue

            # --- LÓGICA DE RECURRENCIA (Mantenemos la anterior por si acaso) ---
            elif schedule == 'daily':
                # Lógica simple: si no se ha hecho hoy
                if not clinic.last_backup_at or clinic.last_backup_at.date() < now.date():
                    run_backup = True
            
            elif schedule == 'weekly':
                # Lógica simple: si es domingo y no se ha hecho hoy
                if now.weekday() == 6 and (not clinic.last_backup_at or clinic.last_backup_at.date() < now.date()):
                    run_backup = True

            # --- EJECUCIÓN DEL BACKUP ---
            if run_backup:
                self.perform_backup(clinic)

        self.stdout.write(self.style.SUCCESS("✅ Verificación de backups finalizada."))

    def perform_backup(self, clinic):
        """Función auxiliar para realizar el backup"""
        try:
            self.stdout.write(f"📦 Iniciando backup para: {clinic.name}...")
            
            with schema_context(clinic.schema_name):
                # Reutilizar lógica de vista
                view_logic = CreateBackupView()
                schema_name = clinic.schema_name
                timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S')

                try:
                    # Intentar PG Dump
                    backup_data_bytes = view_logic._create_pg_dump_bytes(schema_name)
                    file_name = f"auto-sql-{schema_name}-{timestamp}.sql"
                except Exception as e_sql:
                    # Fallback a JSON
                    logger.warning(f"[AutoBackup] pg_dump falló: {e_sql}")
                    backup_data_bytes = view_logic._create_django_dump_bytes()
                    file_name = f"auto-json-{schema_name}-{timestamp}.json"
                
                # Subir a Supabase
                file_path_in_bucket = f"{schema_name}/{file_name}"
                upload_result = upload_backup_to_supabase(backup_data_bytes, file_path_in_bucket)

                if upload_result['success']:
                    # Registrar en BD
                    BackupRecord.objects.create(
                        file_name=file_name,
                        file_path=upload_result['path'],
                        file_size=len(backup_data_bytes),
                        backup_type='automatic',
                        created_by=None
                    )
                    self.stdout.write(f"   -> Subido exitosamente a Supabase")
                    
                    # ACTUALIZAR EL MODELO CLINIC
                    clinic.last_backup_at = timezone.now()
                    
                    # IMPORTANTE: Si era programado, limpiamos la fecha para que no se repita infinitamente
                    if clinic.backup_schedule == 'scheduled':
                        clinic.next_scheduled_backup = None 
                        clinic.backup_schedule = 'disabled' # Opcional: Volver a disabled tras ejecutar
                    
                    clinic.save()
                else:
                    logger.error(f"[AutoBackup] Falló subida para {clinic.name}")

        except Exception as e:
            logger.error(f"[AutoBackup] Error crítico en {clinic.name}: {e}")
            self.stdout.write(self.style.ERROR(f"   -> Error: {e}"))