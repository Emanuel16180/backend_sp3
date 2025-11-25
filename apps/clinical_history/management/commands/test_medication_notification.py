# apps/clinical_history/management/commands/test_medication_notification.py
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from datetime import timedelta
from django_tenants.utils import schema_context
from apps.tenants.models import Clinic
from apps.clinical_history.models import Prescription, MedicationReminder
from apps.notifications.fcm_service import send_fcm_to_multiple
from apps.notifications.models import PushSubscription

User = get_user_model()

class Command(BaseCommand):
    help = 'Envía notificación de prueba de medicamento y crea recordatorio para próximos 5 minutos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='nuevo.paciente@test.com',
            help='Email del paciente'
        )
        parser.add_argument(
            '--tenant',
            type=str,
            default='bienestar',
            help='Schema del tenant (bienestar, mindcare)'
        )
        parser.add_argument(
            '--minutes',
            type=int,
            default=5,
            help='Minutos en el futuro para el recordatorio (default: 5)'
        )

    def handle(self, *args, **options):
        email = options['email']
        tenant_schema = options['tenant']
        minutes = options['minutes']
        
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS("🧪 TEST DE NOTIFICACIÓN DE MEDICAMENTO"))
        self.stdout.write("=" * 60)
        
        try:
            # Obtener tenant
            tenant = Clinic.objects.get(schema_name=tenant_schema)
            self.stdout.write(f"✅ Tenant: {tenant.name} ({tenant.schema_name})")
            
            with schema_context(tenant.schema_name):
                # Buscar paciente
                try:
                    patient = User.objects.get(email=email)
                    self.stdout.write(f"✅ Paciente: {patient.get_full_name()} ({patient.email})")
                except User.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f"❌ Paciente no encontrado: {email}"))
                    return
                
                # Buscar prescripción
                prescription = Prescription.objects.filter(patient=patient).first()
                if not prescription:
                    self.stdout.write(self.style.ERROR(f"❌ No hay prescripciones para {patient.email}"))
                    return
                
                self.stdout.write(f"✅ Medicamento: {prescription.medication} {prescription.dosage}")
                
                # Crear recordatorio para X minutos en el futuro
                now = timezone.now()
                future_time = now + timedelta(minutes=minutes)
                reminder_time = future_time.time()
                today = now.weekday()
                
                # Eliminar recordatorios antiguos
                old_count = MedicationReminder.objects.filter(prescription=prescription).count()
                MedicationReminder.objects.filter(prescription=prescription).delete()
                
                # Crear nuevo recordatorio
                reminder = MedicationReminder.objects.create(
                    prescription=prescription,
                    time=reminder_time,
                    days_of_week=[today],
                    is_active=True,
                    send_notification=True,
                    last_sent=None  # Resetear para que pueda enviarse
                )
                
                self.stdout.write(f"✅ Recordatorios eliminados: {old_count}")
                self.stdout.write(f"✅ Nuevo recordatorio creado:")
                self.stdout.write(f"   ⏰ Hora: {reminder_time.strftime('%H:%M')} UTC")
                self.stdout.write(f"   📅 Día: {today} ({['Lun','Mar','Mié','Jue','Vie','Sáb','Dom'][today]})")
                self.stdout.write(f"   🕐 Se enviará en {minutes} minutos")
                
                # Obtener tokens FCM del paciente
                fcm_subscriptions = PushSubscription.objects.filter(
                    user=patient,
                    is_active=True,
                    fcm_token__isnull=False,
                    platform__in=['android', 'ios']
                )
                
                if not fcm_subscriptions.exists():
                    self.stdout.write(self.style.WARNING(
                        f"⚠️  No hay tokens FCM activos para {patient.email}"
                    ))
                    self.stdout.write("   El recordatorio fue creado pero no se puede enviar notificación ahora")
                    return
                
                fcm_tokens = list(fcm_subscriptions.values_list('fcm_token', flat=True))
                self.stdout.write(f"✅ Tokens FCM encontrados: {len(fcm_tokens)}")
                
                # Enviar notificación de prueba AHORA
                self.stdout.write("\n" + "=" * 60)
                self.stdout.write("📤 ENVIANDO NOTIFICACIÓN DE PRUEBA INMEDIATA...")
                self.stdout.write("=" * 60)
                
                title = "🧪 Test - Recordatorio de Medicamento"
                body = f"{prescription.medication} {prescription.dosage} - {prescription.frequency}"
                
                result = send_fcm_to_multiple(
                    fcm_tokens=fcm_tokens,
                    title=title,
                    body=body,
                    data={
                        'type': 'medication_reminder_test',
                        'prescription_id': str(prescription.id),
                        'medication': prescription.medication,
                        'test': 'true'
                    }
                )
                
                if result['success_count'] > 0:
                    self.stdout.write(self.style.SUCCESS(
                        f"✅ Notificación enviada a {result['success_count']} dispositivo(s)"
                    ))
                    
                    # Mostrar detalles de respuestas
                    for i, response in enumerate(result['responses']):
                        if response['success']:
                            self.stdout.write(
                                f"   ✅ Token {i+1}: {response['message_id'][:50]}..."
                            )
                        else:
                            self.stdout.write(self.style.WARNING(
                                f"   ❌ Token {i+1}: {response['error']}"
                            ))
                else:
                    self.stdout.write(self.style.ERROR(
                        f"❌ No se pudo enviar la notificación"
                    ))
                    if result.get('responses'):
                        for response in result['responses']:
                            if not response['success']:
                                self.stdout.write(f"   Error: {response['error']}")
                
                # Resumen final
                self.stdout.write("\n" + "=" * 60)
                self.stdout.write(self.style.SUCCESS("✅ RESUMEN"))
                self.stdout.write("=" * 60)
                self.stdout.write(f"📱 Notificación inmediata: {'Enviada' if result['success_count'] > 0 else 'Fallida'}")
                self.stdout.write(f"⏰ Recordatorio programado: {reminder_time.strftime('%H:%M')} UTC")
                self.stdout.write(f"🤖 Cron job ejecutará en ~{minutes} minutos")
                self.stdout.write(f"🔄 El recordatorio se enviará automáticamente cada vez que se cumpla la hora")
                self.stdout.write("=" * 60)
                
        except Clinic.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Tenant no encontrado: {tenant_schema}"))
            self.stdout.write("   Tenants disponibles: bienestar, mindcare")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {str(e)}"))
            import traceback
            self.stdout.write(traceback.format_exc())
