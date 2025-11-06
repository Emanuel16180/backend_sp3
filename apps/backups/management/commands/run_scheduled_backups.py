# apps/backups/management/commands/run_scheduled_backups.py

import logging
from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context
from apps.tenants.models import Clinic
from apps.backups.models import BackupRecord
from apps.backups.supabase_storage import upload_backup_to_supabase
from apps.backups.views import CreateBackupView # Reutilizamos la lógica
from django.utils import timezone
import datetime
from io import StringIO

logger = logging.getLogger('apps')

class Command(BaseCommand):
    help = 'Ejecuta los backups automáticos programados para cada clínica.'

    def handle(self, *args, **options):
        self.stdout.write("Iniciando tarea de backups automáticos...")
        
        # 1. Obtener todas las clínicas (desde el schema 'public')
        clinics = Clinic.objects.exclude(schema_name='public')
        
        today = timezone.now().date()
        today_weekday = today.weekday() # Lunes es 0, Domingo es 6
        
        for clinic in clinics:
            schedule = clinic.backup_schedule
            if schedule == 'disabled':
                continue

            # 2. Decidir si hoy toca backup
            run_backup = False
            if schedule == 'daily':
                run_backup = True
            elif schedule == 'weekly' and today_weekday == 6: # 6 = Domingo
                run_backup = True
            
            # (Opcional) Evitar correr si ya se hizo uno hoy
            if clinic.last_backup_at and clinic.last_backup_at.date() == today:
                run_backup = False 

            if not run_backup:
                continue

            self.stdout.write(f"Procesando backup para: {clinic.name}...")

            try:
                # 3. Entrar en el schema de la clínica
                with schema_context(clinic.schema_name):
                    
                    # 4. Reutilizar la lógica de 'CreateBackupView'
                    view_logic = CreateBackupView()
                    backup_data_bytes = None
                    file_type = ""
                    schema_name = clinic.schema_name
                    timestamp = datetime.datetime.now().strftime('%Y-%m-%d-%H%M%S')

                    try:
                        backup_data_bytes = view_logic._create_pg_dump_bytes(schema_name)
                        file_name = f"auto-sql-{schema_name}-{timestamp}.sql"
                    except Exception as e_sql:
                        logger.warning(f"[AutoBackup] pg_dump falló para {schema_name}: {e_sql}")
                        backup_data_bytes = view_logic._create_django_dump_bytes()
                        file_name = f"auto-json-{schema_name}-{timestamp}.json"
                    
                    # 5. Subir a Supabase
                    file_path_in_bucket = f"{schema_name}/{file_name}"
                    upload_result = upload_backup_to_supabase(backup_data_bytes, file_path_in_bucket)

                    if not upload_result['success']:
                        logger.error(f"[AutoBackup] Falló la subida a Supabase para {schema_name}")
                        continue
                        
                    # 6. Crear el registro en la BD del tenant
                    BackupRecord.objects.create(
                        file_name=file_name,
                        file_path=upload_result['path'],
                        file_size=len(backup_data_bytes),
                        backup_type='automatic',
                        created_by=None # Es automático
                    )
                    
                    self.stdout.write(f"  -> ¡Backup automático para {schema_name} creado y subido!")

                # 7. Actualizar la fecha en el modelo Clinic (en 'public')
                clinic.last_backup_at = timezone.now()
                clinic.save()

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  -> Falló el backup para {clinic.name}: {e}"))
        
        self.stdout.write(self.style.SUCCESS("Tarea de backups automáticos finalizada."))