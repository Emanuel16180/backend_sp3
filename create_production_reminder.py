"""
Script para crear prescripción y recordatorio en PRODUCCIÓN
Ejecutar en Render Shell: python create_production_reminder.py
"""
import os
import django
from datetime import time, datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from apps.tenants.models import Clinic
from apps.users.models import CustomUser
from apps.clinical_history.models import Prescription, MedicationReminder

def create_production_data():
    tenant = Clinic.objects.get(schema_name='bienestar')
    
    with schema_context(tenant.schema_name):
        print(f"\n🏥 Trabajando en tenant: {tenant.schema_name}")
        
        # Buscar Ana Torres
        ana = CustomUser.objects.get(email='ana.torres@example.com')
        print(f"✅ Paciente: {ana.get_full_name()} (ID: {ana.id})")
        
        # Buscar profesional
        professional = CustomUser.objects.filter(user_type='professional').first()
        print(f"✅ Profesional: {professional.get_full_name()} (ID: {professional.id})")
        
        # Crear prescripción
        prescription = Prescription.objects.create(
            patient=ana,
            psychiatrist=professional,
            medication_name='Sertralina',
            dosage='50mg',
            frequency='1 vez al día por la mañana',
            notes='Tomar con el desayuno. Evitar alcohol.',
            is_active=True
        )
        print(f"✅ Prescripción creada: ID {prescription.id}")
        
        # Recordatorio en 3 minutos
        now = datetime.now()
        reminder_time = (now + timedelta(minutes=3)).time()
        current_weekday = now.weekday()
        
        reminder = MedicationReminder.objects.create(
            prescription=prescription,
            time=reminder_time,
            days_of_week=[current_weekday],  # Solo hoy
            is_active=True,
            send_notification=True
        )
        
        print(f"\n✅ Recordatorio creado: ID {reminder.id}")
        print(f"   ⏰ Hora: {reminder_time.strftime('%H:%M')}")
        print(f"   📅 Día: {current_weekday}")
        print(f"\n🔔 Ejecuta ahora:")
        print(f"   python manage.py send_medication_reminders")

if __name__ == '__main__':
    create_production_data()
