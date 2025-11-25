"""
Script para crear una prescripción de prueba y un recordatorio para Ana Torres
"""
import os
import sys
import django
from datetime import time, datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from apps.tenants.models import Clinic
from apps.users.models import CustomUser
from apps.clinical_history.models import Prescription, MedicationReminder

def create_test_data():
    # Usar tenant bienestar
    tenant = Clinic.objects.get(schema_name='bienestar')
    
    with schema_context(tenant.schema_name):
        print(f"\n🏥 Trabajando en tenant: {tenant.schema_name}")
        
        # Buscar Ana Torres
        try:
            ana = CustomUser.objects.get(email='ana.torres@example.com')
            print(f"✅ Paciente encontrada: {ana.get_full_name()} (ID: {ana.id})")
        except CustomUser.DoesNotExist:
            print("❌ Ana Torres no encontrada")
            return
        
        # Buscar cualquier profesional para crear la prescripción
        psychiatrist = CustomUser.objects.filter(user_type='professional').first()
        
        if not psychiatrist:
            print("❌ No hay profesionales en el sistema")
            return
        
        print(f"✅ Psiquiatra: {psychiatrist.get_full_name()} (ID: {psychiatrist.id})")
        
        # Crear prescripción
        prescription = Prescription.objects.create(
            patient=ana,
            psychiatrist=psychiatrist,
            medication_name='Sertralina',
            dosage='50mg',
            frequency='1 vez al día por la mañana',
            notes='Tomar con el desayuno. Evitar alcohol.',
            is_active=True
        )
        print(f"✅ Prescripción creada: {prescription.medication_name} {prescription.dosage}")
        
        # Calcular hora de recordatorio (en 2 minutos desde ahora)
        now = datetime.now()
        reminder_time = (now + timedelta(minutes=2)).time()
        current_weekday = now.weekday()  # Día actual de la semana
        
        # Crear recordatorio para HOY y los próximos días
        reminder = MedicationReminder.objects.create(
            prescription=prescription,
            time=reminder_time,
            days_of_week=[current_weekday, (current_weekday + 1) % 7],  # Hoy y mañana
            is_active=True,
            send_notification=True
        )
        
        print(f"✅ Recordatorio creado:")
        print(f"   ⏰ Hora: {reminder_time.strftime('%H:%M')}")
        print(f"   📅 Días: {reminder.days_of_week}")
        print(f"   💊 Medicamento: {prescription.medication_name}")
        print(f"\n🔔 El recordatorio se enviará en aproximadamente 2 minutos")
        print(f"   Asegúrate de que Ana esté suscrita a las notificaciones push")
        print(f"\n📌 Para enviar ahora mismo, ejecuta:")
        print(f"   python manage.py send_medication_reminders")

if __name__ == '__main__':
    create_test_data()
