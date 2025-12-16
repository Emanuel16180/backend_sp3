"""
Script para poblar la base de datos de PRODUCCIÓN con usuarios de prueba.
⚠️ SOLO AÑADE usuarios, NO elimina ni modifica nada existente.
"""
import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from apps.users.models import CustomUser

print("=" * 80)
print("🚀 SCRIPT DE POBLACIÓN DE USUARIOS DE PRODUCCIÓN")
print("=" * 80)
print("⚠️  Este script SOLO AÑADE usuarios, NO elimina nada existente")
print("=" * 80)

def create_users_if_not_exist(tenant_name):
    """Crear usuarios solo si no existen"""
    print(f"\n👤 Creando usuarios en {tenant_name}...")
    
    users_created = 0
    
    # Admin
    if not CustomUser.objects.filter(email=f'admin@{tenant_name}.com').exists():
        admin = CustomUser(
            email=f'admin@{tenant_name}.com',
            username=f'admin_{tenant_name}',
            first_name='Admin',
            last_name=tenant_name.capitalize(),
            user_type='admin',
            is_staff=True,
            is_superuser=True
        )
        admin.set_password('admin123')
        admin.save()
        print(f'  ✅ Admin creado: admin@{tenant_name}.com')
        users_created += 1
    else:
        print(f'  ⏭️  Admin ya existe: admin@{tenant_name}.com')
    
    # Profesionales
    professionals_data = [
        {
            'email': f'dra.martinez@{tenant_name}.com',
            'username': f'dra_martinez_{tenant_name}',
            'first_name': 'Laura',
            'last_name': 'Martínez',
            'specialty': 'Psicología Clínica',
            'license': 'PSI-12345'
        },
        {
            'email': f'dr.garcia@{tenant_name}.com',
            'username': f'dr_garcia_{tenant_name}',
            'first_name': 'Carlos',
            'last_name': 'García',
            'specialty': 'Psiquiatría',
            'license': 'PSI-54321'
        },
        {
            'email': f'lic.rodriguez@{tenant_name}.com',
            'username': f'lic_rodriguez_{tenant_name}',
            'first_name': 'Ana',
            'last_name': 'Rodríguez',
            'specialty': 'Terapia Familiar',
            'license': 'PSI-67890'
        }
    ]
    
    for prof_data in professionals_data:
        if not CustomUser.objects.filter(email=prof_data['email']).exists():
            user = CustomUser(
                email=prof_data['email'],
                username=prof_data['username'],
                first_name=prof_data['first_name'],
                last_name=prof_data['last_name'],
                user_type='professional'
            )
            user.set_password('demo123')
            user.save()
            
            # Crear perfil de profesional
            Professional.objects.create(
                user=user,
                license_number=prof_data['license'],
                bio=f"Profesional especializado en {prof_data['specialty']}",
                years_of_experience=5,
                hourly_rate=50.00
            )
            print(f'  ✅ Profesional creado: {prof_data["email"]}')
            users_created += 1
        else:
            print(f'  ⏭️  Profesional ya existe: {prof_data["email"]}')
    
    # Pacientes
    patients_data = [
        {'email': f'juan.perez@example.com', 'username': f'juan_perez_{tenant_name}', 'first_name': 'Juan', 'last_name': 'Pérez'},
        {'email': f'maria.lopez@example.com', 'username': f'maria_lopez_{tenant_name}', 'first_name': 'María', 'last_name': 'López'},
        {'email': f'pedro.sanchez@example.com', 'username': f'pedro_sanchez_{tenant_name}', 'first_name': 'Pedro', 'last_name': 'Sánchez'},
        {'email': f'ana.gomez@example.com', 'username': f'ana_gomez_{tenant_name}', 'first_name': 'Ana', 'last_name': 'Gómez'},
        {'email': f'luis.fernandez@example.com', 'username': f'luis_fernandez_{tenant_name}', 'first_name': 'Luis', 'last_name': 'Fernández'},
    ]
    
    for patient_data in patients_data:
        if not CustomUser.objects.filter(email=patient_data['email']).exists():
            user = CustomUser(
                email=patient_data['email'],
                username=patient_data['username'],
                first_name=patient_data['first_name'],
                last_name=patient_data['last_name'],
                user_type='patient'
            )
            user.set_password('demo123')
            user.save()
            print(f'  ✅ Paciente creado: {patient_data["email"]}')
            users_created += 1
        else:
            print(f'  ⏭️  Paciente ya existe: {patient_data["email"]}')
    
    return users_created


def create_specialties_if_not_exist():
    """Crear especialidades si no existen"""
    print("\n🏥 Creando especialidades...")
    
    specialties = [
        'Psicología Clínica',
        'Psiquiatría',
        'Terapia Familiar',
        'Psicología Infantil',
        'Terapia de Pareja',
        'Psicología Organizacional'
    ]
    
    created = 0
    for spec_name in specialties:
        _, created_now = Specialty.objects.get_or_create(
            name=spec_name,
            defaults={'description': f'Especialidad en {spec_name}'}
        )
        if created_now:
            print(f'  ✅ Especialidad creada: {spec_name}')
            created += 1
        else:
            print(f'  ⏭️  Especialidad ya existe: {spec_name}')
    
    return created


def create_appointments_if_not_many(tenant_name):
    """Crear citas de ejemplo si hay pocas"""
    print(f"\n📅 Creando citas en {tenant_name}...")
    
    existing_count = Appointment.objects.count()
    if existing_count > 10:
        print(f'  ℹ️  Ya hay {existing_count} citas. No se crearán más.')
        return 0
    
    professionals = Professional.objects.all()[:2]
    patients = CustomUser.objects.filter(user_type='patient')[:3]
    
    if not professionals.exists() or not patients.exists():
        print('  ⚠️  No hay profesionales o pacientes para crear citas')
        return 0
    
    created = 0
    base_date = timezone.now().replace(hour=9, minute=0, second=0, microsecond=0)
    
    for i in range(5):
        appointment_date = base_date + timedelta(days=i, hours=i % 8)
        
        appointment = Appointment.objects.create(
            patient=patients[i % len(patients)],
            professional=professionals[i % len(professionals)],
            scheduled_time=appointment_date,
            duration_minutes=60,
            appointment_type='first_time',
            status='scheduled',
            modality='in_person',
            notes=f'Cita de prueba #{i+1}'
        )
        print(f'  ✅ Cita creada: {appointment.patient.get_full_name()} con {appointment.professional.user.get_full_name()}')
        created += 1
    
    return created


def create_session_notes_if_not_many(tenant_name):
    """Crear notas de sesión de ejemplo"""
    print(f"\n📝 Creando notas de sesión en {tenant_name}...")
    
    existing_count = SessionNote.objects.count()
    if existing_count > 5:
        print(f'  ℹ️  Ya hay {existing_count} notas. No se crearán más.')
        return 0
    
    appointments = Appointment.objects.filter(status='completed')[:3]
    
    if not appointments.exists():
        # Marcar algunas citas como completadas
        pending_appointments = Appointment.objects.filter(status='scheduled')[:3]
        for apt in pending_appointments:
            apt.status = 'completed'
            apt.save()
        appointments = pending_appointments
    
    created = 0
    for appointment in appointments:
        if not SessionNote.objects.filter(appointment=appointment).exists():
            SessionNote.objects.create(
                appointment=appointment,
                professional=appointment.professional,
                patient=appointment.patient,
                session_date=appointment.scheduled_time.date(),
                duration_minutes=appointment.duration_minutes,
                main_topic='Evaluación inicial',
                observations='Paciente muestra buena disposición al tratamiento.',
                treatment_plan='Continuar con sesiones semanales.',
                next_session_plan='Trabajar en técnicas de relajación.',
                patient_progress='Adecuado',
                notes='Sesión productiva.'
            )
            print(f'  ✅ Nota creada para cita de {appointment.patient.get_full_name()}')
            created += 1
    
    return created


# EJECUTAR PARA CADA TENANT
tenants = ['bienestar', 'mindcare']

total_users = 0
total_specialties = 0
total_appointments = 0
total_notes = 0

for tenant in tenants:
    print(f"\n{'='*80}")
    print(f"🏢 PROCESANDO TENANT: {tenant.upper()}")
    print(f"{'='*80}")
    
    with schema_context(tenant):
        try:
            total_users += create_users_if_not_exist(tenant)
            total_specialties += create_specialties_if_not_exist()
            total_appointments += create_appointments_if_not_many(tenant)
            total_notes += create_session_notes_if_not_many(tenant)
        except Exception as e:
            print(f"❌ Error en {tenant}: {str(e)}")
            import traceback
            traceback.print_exc()

# RESUMEN FINAL
print("\n" + "=" * 80)
print("✅ POBLACIÓN COMPLETADA")
print("=" * 80)
print(f"📊 Resumen:")
print(f"   • Usuarios creados: {total_users}")
print(f"   • Especialidades creadas: {total_specialties}")
print(f"   • Citas creadas: {total_appointments}")
print(f"   • Notas de sesión creadas: {total_notes}")
print("=" * 80)
print("\n🎉 ¡Base de datos poblada exitosamente!")
print("\n🔑 CREDENCIALES DE PRUEBA:")
print("=" * 80)
for tenant in tenants:
    print(f"\n{tenant.upper()}:")
    print(f"  Admin:        admin@{tenant}.com / admin123")
    print(f"  Profesional:  dra.martinez@{tenant}.com / demo123")
    print(f"  Paciente:     juan.perez@example.com / demo123")
print("=" * 80)
