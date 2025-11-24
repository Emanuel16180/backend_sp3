"""
Script para resetear last_sent de recordatorios de medicamentos
Ejecutar en Render: python reset_reminder_last_sent.py
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from apps.tenants.models import Clinic
from apps.clinical_history.models import MedicationReminder

tenant = Clinic.objects.get(schema_name='bienestar')

with schema_context(tenant.schema_name):
    reminders = MedicationReminder.objects.filter(is_active=True)
    
    for reminder in reminders:
        print(f"Recordatorio ID {reminder.id}: {reminder.prescription.medication_name}")
        print(f"  Último envío: {reminder.last_sent}")
        reminder.last_sent = None
        reminder.save()
        print(f"  ✅ Reseteado")
    
    print(f"\n✅ {reminders.count()} recordatorios reseteados")
