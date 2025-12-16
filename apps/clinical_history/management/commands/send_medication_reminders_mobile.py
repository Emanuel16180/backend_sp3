#!/usr/bin/env python
"""
Comando Django para enviar recordatorios de medicamentos via FCM (móvil).
Se ejecuta periódicamente (cada 15 minutos) mediante un Cron Job en Render.

Uso:
    python manage.py send_medication_reminders_mobile
    python manage.py send_medication_reminders_mobile --window 20
    python manage.py send_medication_reminders_mobile --tenant bienestar
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from apps.clinical_history.models import MedicationReminder
from apps.notifications.fcm_service import send_fcm_to_multiple
from apps.notifications.models import PushSubscription
from django_tenants.utils import schema_context, get_tenant_model
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Envía recordatorios de medicamentos vía notificaciones push FCM (móvil)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--window',
            type=int,
            default=15,
            help='Ventana de tiempo en minutos (default: 15)'
        )
        parser.add_argument(
            '--tenant',
            type=str,
            help='Procesar solo un tenant específico'
        )

    def handle(self, *args, **options):
        window_minutes = options['window']
        specific_tenant = options.get('tenant')
        
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("🔔 RECORDATORIOS DE MEDICAMENTOS - MÓVIL (FCM)"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"⏰ Hora actual: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.stdout.write(f"📊 Ventana de tiempo: ±{window_minutes} minutos")
        self.stdout.write("")
        
        # Obtener todos los tenants
        Tenant = get_tenant_model()
        
        if specific_tenant:
            tenants = Tenant.objects.filter(schema_name=specific_tenant)
            if not tenants.exists():
                self.stdout.write(self.style.ERROR(f"❌ Tenant '{specific_tenant}' no encontrado"))
                return
        else:
            # Excluir el tenant 'public'
            tenants = Tenant.objects.exclude(schema_name='public')
        
        total_sent = 0
        total_failed = 0
        total_tenants = tenants.count()
        
        self.stdout.write(f"🏢 Procesando {total_tenants} tenant(s)...")
        self.stdout.write("")
        
        # Procesar cada tenant
        for tenant in tenants:
            self.stdout.write(f"\n{'='*60}")
            self.stdout.write(f"🏥 Tenant: {tenant.schema_name} ({tenant.name})")
            self.stdout.write(f"{'='*60}")
            
            with schema_context(tenant.schema_name):
                sent, failed = self._process_reminders(window_minutes)
                total_sent += sent
                total_failed += failed
        
        # Resumen final
        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("✅ PROCESO COMPLETADO"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"📊 Total enviados: {total_sent}")
        self.stdout.write(f"❌ Total fallidos: {total_failed}")
        self.stdout.write(f"🏢 Tenants procesados: {total_tenants}")
        self.stdout.write("=" * 60)

    def _process_reminders(self, window_minutes):
        """
        Procesa recordatorios para el tenant actual.
        Retorna (sent_count, failed_count)
        """
        now = timezone.now()
        current_time = now.time()
        current_weekday = now.weekday()  # 0=Lunes, 6=Domingo
        
        # Calcular ventana de tiempo
        window_start = (datetime.combine(datetime.today(), current_time) - timedelta(minutes=window_minutes)).time()
        window_end = (datetime.combine(datetime.today(), current_time) + timedelta(minutes=window_minutes)).time()
        
        self.stdout.write(f"   📅 Día de la semana: {current_weekday} ({['Lun','Mar','Mié','Jue','Vie','Sáb','Dom'][current_weekday]})")
        self.stdout.write(f"   ⏰ Ventana: {window_start.strftime('%H:%M')} - {window_end.strftime('%H:%M')}")
        self.stdout.write("")
        
        # Buscar recordatorios pendientes
        reminders = MedicationReminder.objects.filter(
            is_active=True,
            send_notification=True,
            prescription__is_active=True,
            time__gte=window_start,
            time__lte=window_end
        ).select_related('prescription', 'prescription__patient')
        
        # Filtrar por día de la semana
        pending_reminders = []
        for reminder in reminders:
            if current_weekday in reminder.days_of_week:
                # Verificar si ya se envió hoy
                if reminder.last_sent:
                    last_sent_date = timezone.localtime(reminder.last_sent).date()
                    today = now.date()
                    if last_sent_date >= today:
                        self.stdout.write(
                            f"   ⏭️  Ya enviado hoy: {reminder.prescription.medication_name} "
                            f"({reminder.time.strftime('%H:%M')}) a {reminder.prescription.patient.email}"
                        )
                        continue
                
                pending_reminders.append(reminder)
        
        if not pending_reminders:
            self.stdout.write(self.style.WARNING("   ℹ️  No hay recordatorios pendientes en esta ventana"))
            return 0, 0
        
        self.stdout.write(f"   📬 {len(pending_reminders)} recordatorio(s) pendiente(s)")
        self.stdout.write("")
        
        sent_count = 0
        failed_count = 0
        
        # Procesar cada recordatorio
        for reminder in pending_reminders:
            patient = reminder.prescription.patient
            medication = reminder.prescription.medication_name
            dosage = reminder.prescription.dosage
            time_str = reminder.time.strftime('%H:%M')
            
            self.stdout.write(f"   📤 Procesando: {medication} para {patient.get_full_name()} ({patient.email})")
            
            # Buscar tokens FCM del paciente (solo móvil)
            fcm_subscriptions = PushSubscription.objects.filter(
                user=patient,
                is_active=True,
                fcm_token__isnull=False,
                platform__in=['android', 'ios']
            )
            
            if not fcm_subscriptions.exists():
                self.stdout.write(
                    self.style.WARNING(f"      ⚠️  {patient.email} no tiene dispositivos móviles registrados")
                )
                failed_count += 1
                continue
            
            # Recopilar tokens FCM
            fcm_tokens = [sub.fcm_token for sub in fcm_subscriptions]
            
            # Preparar notificación
            title = f"💊 Recordatorio de Medicamento"
            body = f"Hora de tomar {medication} ({dosage})"
            data = {
                'type': 'medication_reminder',
                'medication_id': str(reminder.prescription.id),
                'medication_name': medication,
                'dosage': dosage,
                'time': time_str,
                'url': '/medications'
            }
            
            # Enviar notificación FCM
            result = send_fcm_to_multiple(fcm_tokens, title, body, data)
            
            if result['success_count'] > 0:
                # Actualizar last_sent
                reminder.last_sent = now
                reminder.save(update_fields=['last_sent'])
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"      ✅ Enviado a {result['success_count']} dispositivo(s)"
                    )
                )
                sent_count += 1
            else:
                self.stdout.write(
                    self.style.ERROR(
                        f"      ❌ Falló el envío a todos los dispositivos"
                    )
                )
                failed_count += 1
            
            # Desactivar tokens inválidos
            for i, response in enumerate(result.get('responses', [])):
                if not response['success'] and response.get('error'):
                    error = response['error'].lower()
                    if 'not registered' in error or 'invalid' in error:
                        subscription = fcm_subscriptions[i]
                        subscription.is_active = False
                        subscription.save(update_fields=['is_active'])
                        self.stdout.write(
                            self.style.WARNING(
                                f"      🗑️  Token inválido desactivado: {subscription.fcm_token[:20]}..."
                            )
                        )
        
        return sent_count, failed_count
