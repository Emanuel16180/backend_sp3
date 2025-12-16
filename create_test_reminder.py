"""
Script interactivo para crear un recordatorio de medicamento de prueba
Funciona en PRODUCCIÓN con la base de datos de Render
"""
import os
import django
from datetime import datetime, timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.notifications.models import PushSubscription
from apps.clinical_history.models import MedicalPrescription, MedicationReminder
from django_tenants.utils import schema_context
from apps.tenants.models import Clinic

User = get_user_model()

print("\n" + "="*70)
print("🏥 CREADOR DE RECORDATORIO DE MEDICAMENTO - PASO A PASO")
print("="*70)

# PASO 1: Seleccionar tenant
print("\n🏢 PASO 1: Selecciona la clínica")
print("-"*70)

tenants = Clinic.objects.exclude(schema_name='public').order_by('name')
print()
for i, tenant in enumerate(tenants, 1):
    print(f"   {i}. {tenant.name} ({tenant.schema_name})")

while True:
    try:
        choice = input(f"\nEscribe el número de la clínica (1-{tenants.count()}): ").strip()
        choice = int(choice)
        if 1 <= choice <= tenants.count():
            selected_tenant = list(tenants)[choice-1]
            break
        else:
            print(f"❌ Por favor escribe un número entre 1 y {tenants.count()}")
    except ValueError:
        print("❌ Por favor escribe un número válido")

print(f"\n✅ Seleccionado: {selected_tenant.name}")

# Trabajar dentro del tenant seleccionado
with schema_context(selected_tenant.schema_name):
    
    # PASO 2: Verificar pacientes con app móvil
    print("\n📱 PASO 2: Buscando pacientes con app móvil instalada...")
    print("-"*70)
    
    mobile_subs = PushSubscription.objects.filter(
        platform='mobile',
        is_active=True
    ).select_related('user')
    
    if not mobile_subs.exists():
        print("\n❌ ERROR: No hay pacientes con la app móvil instalada")
        print("\n💡 Solución:")
        print("   1. Abre la app Flutter en tu celular")
        print("   2. Inicia sesión con un paciente")
        print("   3. Vuelve a ejecutar este script")
        exit(1)
    
    print(f"\n✅ Encontrados {mobile_subs.count()} dispositivo(s) móvil(es):\n")
    
    patients = {}
    for i, sub in enumerate(mobile_subs, 1):
        user = sub.user
        patients[i] = user
        print(f"   {i}. {user.get_full_name()} ({user.email})")
        print(f"      Rol: {user.role}")
        print(f"      Token: {sub.fcm_token[:40]}...")
        print()
    
    # PASO 3: Seleccionar paciente
    print("-"*70)
    print("📋 PASO 3: Selecciona un paciente")
    print("-"*70)
    
    while True:
        try:
            choice = input(f"\nEscribe el número del paciente (1-{len(patients)}): ").strip()
            choice = int(choice)
            if choice in patients:
                selected_patient = patients[choice]
                break
            else:
                print(f"❌ Por favor escribe un número entre 1 y {len(patients)}")
        except ValueError:
            print("❌ Por favor escribe un número válido")
    
    print(f"\n✅ Seleccionado: {selected_patient.get_full_name()}")
    
    # PASO 4: Crear prescripción
    print("\n" + "-"*70)
    print("💊 PASO 4: Datos del medicamento")
    print("-"*70)
    
    medication_name = input("\nNombre del medicamento (Enter para 'Paracetamol'): ").strip()
    if not medication_name:
        medication_name = "Paracetamol"
    
    dosage = input("Dosis (Enter para '500mg'): ").strip()
    if not dosage:
        dosage = "500mg"
    
    frequency = input("Frecuencia (Enter para 'Cada 8 horas'): ").strip()
    if not frequency:
        frequency = "Cada 8 horas"
    
    prescription = MedicalPrescription.objects.create(
        patient=selected_patient,
        medication_name=medication_name,
        dosage=dosage,
        frequency=frequency,
        start_date=datetime.now().date(),
        notes="Prescripción de prueba para notificaciones móviles"
    )
    
    print(f"\n✅ Prescripción creada: {medication_name} {dosage}")
    
    # PASO 5: Configurar hora del recordatorio
    print("\n" + "-"*70)
    print("⏰ PASO 5: Configurar hora del recordatorio")
    print("-"*70)
    
    now = datetime.now()
    print(f"\n📍 Hora actual: {now.strftime('%H:%M')}")
    
    # Sugerir hora en 5 minutos
    suggested_time = now + timedelta(minutes=5)
    print(f"💡 Sugerencia: {suggested_time.strftime('%H:%M')} (en 5 minutos)")
    
    time_input = input(f"\nHora del recordatorio HH:MM (Enter para '{suggested_time.strftime('%H:%M')}'): ").strip()
    
    if not time_input:
        reminder_time = suggested_time.time()
    else:
        try:
            hour, minute = time_input.split(':')
            reminder_time = datetime.strptime(f"{hour}:{minute}", "%H:%M").time()
        except:
            print("❌ Formato inválido, usando sugerencia")
            reminder_time = suggested_time.time()
    
    # PASO 6: Configurar días
    print("\n" + "-"*70)
    print("📅 PASO 6: Días de la semana")
    print("-"*70)
    
    days_map = {
        0: "Lunes",
        1: "Martes", 
        2: "Miércoles",
        3: "Jueves",
        4: "Viernes",
        5: "Sábado",
        6: "Domingo"
    }
    
    today = now.weekday()
    print(f"\n📍 Hoy es: {days_map[today]} (día {today})")
    print("\n💡 Días disponibles:")
    for day_num, day_name in days_map.items():
        marker = "👉" if day_num == today else "  "
        print(f"{marker} {day_num}. {day_name}")
    
    days_input = input(f"\nDías separados por comas (Enter para solo hoy '{today}'): ").strip()
    
    if not days_input:
        days_of_week = [today]
    else:
        try:
            days_of_week = [int(d.strip()) for d in days_input.split(',')]
            days_of_week = [d for d in days_of_week if 0 <= d <= 6]
        except:
            print("❌ Formato inválido, usando solo hoy")
            days_of_week = [today]
    
    # PASO 7: Mensaje personalizado
    print("\n" + "-"*70)
    print("💬 PASO 7: Mensaje del recordatorio")
    print("-"*70)
    
    default_message = f"Es hora de tomar tu {medication_name}"
    message = input(f"\nMensaje (Enter para '{default_message}'): ").strip()
    if not message:
        message = default_message
    
    # PASO 8: Crear recordatorio
    print("\n" + "-"*70)
    print("✨ PASO 8: Creando recordatorio...")
    print("-"*70)
    
    reminder = MedicationReminder.objects.create(
        prescription=prescription,
        time=reminder_time,
        days_of_week=days_of_week,
        message=message,
        is_active=True
    )
    
    print("\n" + "="*70)
    print("✅ ¡RECORDATORIO CREADO CON ÉXITO!")
    print("="*70)
    
    print(f"\n📋 RESUMEN:")
    print(f"   Clínica: {selected_tenant.name}")
    print(f"   Paciente: {selected_patient.get_full_name()}")
    print(f"   Medicamento: {medication_name} {dosage}")
    print(f"   Hora: {reminder_time.strftime('%H:%M')}")
    print(f"   Días: {', '.join([days_map[d] for d in days_of_week])}")
    print(f"   Mensaje: {message}")
    
    print("\n⏳ PRÓXIMOS PASOS:")
    print("   1. El cron job corre cada 15 minutos")
    print("   2. Buscará recordatorios en ventana de ±15 minutos")
    print(f"   3. Tu recordatorio se enviará cerca de las {reminder_time.strftime('%H:%M')}")
    print("   4. Recibirás la notificación en tu celular 📱")
    
    print("\n📊 MONITOREO:")
    print("   • Ve a: https://dashboard.render.com")
    print("   • Busca: medication-reminders-mobile")
    print("   • Click en 'Logs' para ver la ejecución")
    
    print("\n" + "="*70)
