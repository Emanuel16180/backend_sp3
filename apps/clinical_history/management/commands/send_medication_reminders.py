"""
Comando de Django para enviar notificaciones de recordatorios de medicamentos.
Ejecutar con: python manage.py send_medication_reminders

Para producción, configurar como cron job o tarea programada cada 5-10 minutos.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
from apps.clinical_history.models import MedicationReminder
from apps.notifications.models import PushSubscription
from pywebpush import webpush, WebPushException
from django.conf import settings
from django_tenants.utils import schema_context, get_tenant_model
from py_vapid import Vapid
import json
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Envía notificaciones push para recordatorios de medicamentos pendientes'

    def handle(self, *args, **options):
        """
        Busca recordatorios que deban enviarse en los próximos 10 minutos
        y envía las notificaciones push correspondientes.
        Ejecuta en todos los tenants activos.
        """
        # Obtener todos los tenants activos (excluyendo el público)
        Tenant = get_tenant_model()
        tenants = Tenant.objects.exclude(schema_name='public')
        
        total_sent = 0
        
        for tenant in tenants:
            self.stdout.write(f'\n🏥 Procesando tenant: {tenant.schema_name}')
            
            with schema_context(tenant.schema_name):
                sent_count = self.process_tenant_reminders()
                total_sent += sent_count
        
        self.stdout.write(
            self.style.SUCCESS(f'\n📊 Total global de notificaciones enviadas: {total_sent}')
        )
    
    def process_tenant_reminders(self):
        """
        Procesa recordatorios para el tenant actual
        """
        now = timezone.now()
        current_time = now.time()
        current_weekday = now.weekday()  # 0=Lunes, 6=Domingo
        
        # Buscar recordatorios activos para hoy
        reminders = MedicationReminder.objects.filter(
            is_active=True,
            send_notification=True,
            prescription__is_active=True
        ).select_related('prescription', 'prescription__patient')
        
        sent_count = 0
        
        for reminder in reminders:
            # Verificar si hoy está en los días programados
            if current_weekday not in reminder.days_of_week:
                continue
            
            # Calcular diferencia de tiempo
            reminder_datetime = datetime.combine(now.date(), reminder.time)
            reminder_datetime = timezone.make_aware(reminder_datetime)
            
            # Solo enviar si falta menos de 10 minutos
            time_diff = reminder_datetime - now
            
            if timedelta(0) <= time_diff <= timedelta(minutes=10):
                # Verificar si ya se envió hoy
                if reminder.last_sent and reminder.last_sent.date() == now.date():
                    continue
                
                # Enviar notificación
                success = self.send_reminder_notification(reminder)
                
                if success:
                    # Actualizar fecha de último envío
                    reminder.last_sent = now
                    reminder.save(update_fields=['last_sent'])
                    sent_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✅ Notificación enviada: {reminder.prescription.medication_name} a {reminder.prescription.patient.email}'
                        )
                    )
        
        if sent_count > 0:
            self.stdout.write(
                self.style.SUCCESS(f'  📨 Notificaciones enviadas en este tenant: {sent_count}')
            )
        
        return sent_count
    
    def send_reminder_notification(self, reminder):
        """
        Envía la notificación push al paciente
        """
        patient = reminder.prescription.patient
        
        # Obtener suscripciones activas del paciente
        subscriptions = PushSubscription.objects.filter(
            user=patient,
            is_active=True
        )
        
        if not subscriptions.exists():
            logger.warning(f'Paciente {patient.email} no tiene suscripciones activas')
            return False
        
        # Preparar payload de la notificación
        payload = {
            'title': f'💊 Recordatorio de Medicamento',
            'body': f'{reminder.prescription.medication_name} - {reminder.prescription.dosage}',
            'icon': '/static/icons/medication.png',
            'badge': '/static/icons/badge.png',
            'url': '/medications',
            'data': {
                'type': 'medication_reminder',
                'reminder_id': reminder.id,
                'prescription_id': reminder.prescription.id,
                'time': reminder.time.strftime('%H:%M')
            }
        }
        
        vapid_claims = {
            "sub": f"mailto:{settings.VAPID_CLAIM_EMAIL}"
        }
        
        # Obtener clave VAPID
        vapid_key = self.get_vapid_key()
        
        # Enviar a cada suscripción
        success = False
        for subscription in subscriptions:
            try:
                webpush(
                    subscription_info=subscription.to_dict(),
                    data=json.dumps(payload),
                    vapid_private_key=vapid_key,
                    vapid_claims=vapid_claims
                )
                
                subscription.last_used = timezone.now()
                subscription.save(update_fields=['last_used'])
                success = True
                
                logger.info(f'✅ Push enviado a {patient.email}')
                
            except WebPushException as e:
                logger.error(f'❌ Error enviando push a {patient.email}: {str(e)}')
                
                # Si el endpoint expiró (410), desactivar suscripción
                if e.response and e.response.status_code == 410:
                    subscription.is_active = False
                    subscription.save(update_fields=['is_active'])
        
        return success
    
    def get_vapid_key(self):
        """
        Obtiene la clave VAPID en el formato correcto.
        Maneja tanto formato PEM como raw base64.
        """
        private_key = settings.VAPID_PRIVATE_KEY.strip()
        
        # Validar que la clave está configurada correctamente
        if not private_key or len(private_key) < 50:
            raise ValueError(
                "VAPID_PRIVATE_KEY no está configurada correctamente. "
                "Debe ser una clave PEM completa o raw base64."
            )
        
        # Si la clave está en formato PEM (completo), convertirla
        if private_key.startswith('-----BEGIN'):
            vapid = Vapid.from_pem(private_key.encode())
            return vapid
        else:
            # Si es formato raw base64 (sin headers), usarla directamente
            # pywebpush espera el string raw
            return private_key
