#!/usr/bin/env python
"""
Repoblación completa con datos realistas y citas
"""

import os
import sys
import django
from faker import Faker
import random
from datetime import datetime, timedelta, time

# Configurar Django
sys.path.append('c:/Users/asus/Documents/psico_admin_sp1_despliegue')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from apps.tenants.models import Clinic
from apps.users.models import CustomUser, PatientProfile
from apps.professionals.models import ProfessionalProfile, Specialization, WorkingHours
from apps.appointments.models import Appointment, PsychologistAvailability

# Configurar Faker en español
fake = Faker('es_ES')
Faker.seed(42)

def normalize_text(text):
    """Normalizar texto para emails y usernames"""
    replacements = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'ñ': 'n', 'Ñ': 'N'
    }
    for original, replacement in replacements.items():
        text = text.replace(original, replacement)
    return text

def create_specializations(clinic_name):
    """Crear especializaciones psicológicas"""
    specializations_data = [
        ("Psicología Clínica", "Tratamiento de trastornos mentales y emocionales"),
        ("Psicología Cognitivo-Conductual", "Terapia centrada en pensamientos y comportamientos"),
        ("Psicología Infantil", "Especialización en niños y adolescentes"),
        ("Psicología de Pareja", "Terapia de relaciones y problemas de pareja"),
        ("Psicología Familiar", "Intervención en dinámicas familiares"),
        ("Neuropsicología", "Evaluación y rehabilitación neuropsicológica"),
        ("Psicología Educativa", "Orientación académica y problemas de aprendizaje"),
        ("Psicología Organizacional", "Bienestar laboral y desarrollo organizacional")
    ]
    
    created_specs = []
    for name, description in specializations_data:
        spec, created = Specialization.objects.get_or_create(
            name=name,
            defaults={'description': description}
        )
        created_specs.append(spec)
    
    print(f"   ✅ {len(created_specs)} especializaciones creadas")
    return created_specs

def create_admin(clinic):
    """Crear administrador de la clínica"""
    admin, created = CustomUser.objects.get_or_create(
        email='admin@gmail.com',
        defaults={
            'first_name': 'Admin',
            'last_name': clinic.name,
            'user_type': 'admin',
            'ci': '99999999',
            'phone': '+591 70000000',
            'gender': 'M',
            'date_of_birth': fake.date_of_birth(minimum_age=30, maximum_age=50),
            'is_staff': True,
            'is_superuser': True,
            'is_active': True
        }
    )
    
    if created:
        admin.set_password('admin')
        admin.save()
        print(f"   👑 Admin creado: {admin.email}")
    else:
        print(f"   👑 Admin existente: {admin.email}")
    
    return admin

def create_patients(clinic_name, count=10):
    """Crear pacientes realistas"""
    print(f"   👥 Creando {count} pacientes...")
    
    patients = []
    for i in range(count):
        first_name = fake.first_name()
        last_name = fake.last_name()
        
        norm_first = normalize_text(first_name)
        norm_last = normalize_text(last_name)
        
        # Agregar un índice único para evitar duplicados
        timestamp = int(datetime.now().timestamp() * 1000) % 10000  # últimos 4 dígitos del timestamp
        email = f"{norm_first.lower()}.{norm_last.lower()}.{i+1}.{timestamp}.{clinic_name}@paciente.com"
        username = f"{norm_first.lower()}.{norm_last.lower()}.{i+1}.{timestamp}.{clinic_name}"
        
        # Crear usuario paciente
        patient = CustomUser.objects.create_user(
            email=email,
            username=username,
            password='paciente123',
            first_name=first_name,
            last_name=last_name,
            user_type='patient',
            phone=fake.phone_number()[:15],
            ci=str(random.randint(1000000, 9999999)),
            gender=random.choice(['M', 'F']),
            date_of_birth=fake.date_of_birth(minimum_age=18, maximum_age=70),
            address=fake.address()[:100]
        )
        
        # Crear perfil de paciente
        PatientProfile.objects.create(
            user=patient,
            emergency_contact_name=fake.name(),
            emergency_contact_phone=str(random.randint(70000000, 79999999)),
            emergency_contact_relationship=random.choice(['Madre', 'Padre', 'Esposo/a', 'Hermano/a', 'Hijo/a']),
            occupation=fake.job(),
            education_level=random.choice(['secundaria', 'tecnico', 'universitario']),
            initial_reason=f"Consulta inicial por {random.choice(['ansiedad', 'depresión', 'estrés', 'problemas familiares', 'orientación'])}",
            how_found_us=random.choice(['Referido médico', 'Internet', 'Familiar', 'Amigo']),
            profile_completed=True
        )
        
        patients.append(patient)
    
    return patients

def create_professionals(clinic_name, specializations, count=5):
    """Crear profesionales con especializaciones y horarios"""
    print(f"   👨‍⚕️ Creando {count} profesionales...")
    
    professionals = []
    for i in range(count):
        first_name = fake.first_name()
        last_name = fake.last_name()
        
        norm_first = normalize_text(first_name)
        norm_last = normalize_text(last_name)
        
        # Agregar índice único
        timestamp = int(datetime.now().timestamp() * 1000) % 10000  # últimos 4 dígitos del timestamp
        email = f"dr.{norm_first.lower()}.{norm_last.lower()}.{i+1}.{timestamp}.{clinic_name}@psicologo.com"
        username = f"dr.{norm_first.lower()}.{norm_last.lower()}.{i+1}.{timestamp}.{clinic_name}"
        
        # Crear usuario profesional
        professional = CustomUser.objects.create_user(
            email=email,
            username=username,
            password='psicologo123',
            first_name=f"Dr. {first_name}",
            last_name=last_name,
            user_type='professional',
            phone=fake.phone_number()[:15],
            ci=str(random.randint(1000000, 9999999)),
            gender=random.choice(['M', 'F']),
            date_of_birth=fake.date_of_birth(minimum_age=25, maximum_age=60),
            address=fake.address()[:100]
        )
        
        # Crear perfil profesional
        profile = ProfessionalProfile.objects.create(
            user=professional,
            license_number=f"PSI-{random.randint(1000, 9999)}",
            bio=f"Psicólogo especializado con {random.randint(3, 20)} años de experiencia en el campo. {fake.text(max_nb_chars=300)}",
            session_duration=random.choice([45, 60, 90]),
            consultation_fee=random.choice([150, 200, 250, 300, 350]),
            experience_years=random.randint(3, 20),
            education=f"Licenciatura en Psicología - Universidad {fake.company()}. Maestría en {random.choice(['Psicología Clínica', 'Neuropsicología', 'Psicología Educativa'])}",
            office_address=fake.address()[:100],
            city=random.choice(['La Paz', 'Santa Cruz', 'Cochabamba']),
            is_verified=True,
            profile_completed=True
        )
        
        # Asignar especializaciones
        selected_specs = random.sample(specializations, k=random.randint(1, 3))
        profile.specializations.set(selected_specs)
        
        # Crear horarios de trabajo (Lunes a Viernes)
        for day in range(5):  # 0=Lunes, 4=Viernes
            start_hour = random.choice([8, 9])
            end_hour = random.choice([17, 18, 19])
            
            WorkingHours.objects.create(
                professional=profile,
                day_of_week=day,
                start_time=time(start_hour),
                end_time=time(end_hour)
            )
            
            # Crear disponibilidad en appointments para cada día
            PsychologistAvailability.objects.create(
                psychologist=professional,
                weekday=day,
                start_time=time(start_hour),
                end_time=time(end_hour),
                blocked_dates=[]  # Sin fechas bloqueadas inicialmente
            )
        
        professionals.append(professional)
    
    return professionals

def create_appointments(patients, professionals, count=20):
    """Crear citas realistas"""
    print(f"   📅 Creando {count} citas...")
    
    # Fechas para las citas (últimos 30 días y próximos 30 días)
    base_date = datetime.now().date()
    
    appointments = []
    for i in range(count):
        patient = random.choice(patients)
        professional = random.choice(professionals)
        
        # Fecha aleatoria en rango de +/- 30 días
        days_offset = random.randint(-30, 30)
        appointment_date = base_date + timedelta(days=days_offset)
        
        # Hora aleatoria de trabajo (9:00 - 17:00)
        hour = random.randint(9, 16)
        minute = random.choice([0, 30])
        appointment_time = time(hour, minute)
        
        # Estado aleatorio pero realista
        if days_offset < -1:  # Citas pasadas
            status = random.choice(['completed', 'completed', 'completed', 'cancelled'])
        elif days_offset < 0:  # Ayer
            status = random.choice(['completed', 'no_show'])
        else:  # Futuras
            status = random.choice(['confirmed', 'confirmed', 'pending'])
        
        try:
            appointment = Appointment.objects.create(
                patient=patient,
                psychologist=professional,
                appointment_date=appointment_date,
                start_time=appointment_time,
                end_time=time(hour + 1, minute),  # 1 hora después
                status=status,
                reason_for_visit=f"Consulta por {random.choice(['ansiedad', 'depresión', 'terapia familiar', 'orientación vocacional', 'estrés laboral'])}",
                appointment_type=random.choice(['online', 'in_person']),
                notes=f"Cita de {patient.first_name} con {professional.first_name}. {fake.sentence()}"
            )
            appointments.append(appointment)
        except Exception as e:
            # Manejar conflictos de horario
            print(f"      ⚠️ Conflicto de horario evitado: {e}")
            continue
    
    return appointments

def populate_clinic(clinic):
    """Poblar una clínica completa con todos los datos"""
    print(f"\n🏥 Poblando {clinic.name} ({clinic.schema_name})")
    
    # Limpiar datos únicos de Faker para esta clínica
    fake.unique.clear()
    
    with schema_context(clinic.schema_name):
        # 1. Crear administrador
        admin = create_admin(clinic)
        
        # 2. Crear especializaciones
        specializations = create_specializations(clinic.name)
        
        # 3. Determinar cantidades según la clínica
        if clinic.schema_name == 'bienestar':
            patient_count = 12
            professional_count = 4
            appointment_count = 25
        else:  # mindcare
            patient_count = 25
            professional_count = 7
            appointment_count = 50
        
        # 4. Crear pacientes
        patients = create_patients(clinic.schema_name, patient_count)
        
        # 5. Crear profesionales
        professionals = create_professionals(clinic.schema_name, specializations, professional_count)
        
        # 6. Crear citas
        appointments = create_appointments(patients, professionals, appointment_count)
        
        # 7. Estadísticas finales
        total_users = CustomUser.objects.count()
        total_patients = CustomUser.objects.filter(user_type='patient').count()
        total_professionals = CustomUser.objects.filter(user_type='professional').count()
        total_admins = CustomUser.objects.filter(user_type='admin').count()
        total_appointments = Appointment.objects.count()
        total_specs = Specialization.objects.count()
        
        print(f"   📊 RESUMEN:")
        print(f"      👥 {total_users} usuarios ({total_patients}P, {total_professionals}Pr, {total_admins}A)")
        print(f"      📅 {total_appointments} citas")
        print(f"      🎓 {total_specs} especializaciones")
        print(f"      ✅ Datos completos y realistas")
        
        return {
            'users': total_users,
            'patients': total_patients,
            'professionals': total_professionals,
            'admins': total_admins,
            'appointments': total_appointments,
            'specializations': total_specs
        }

def main():
    """Función principal"""
    print("🚀 REPOBLACIÓN COMPLETA CON DATOS REALISTAS")
    print("=" * 50)
    
    # Obtener clínicas reales
    clinics = Clinic.objects.exclude(schema_name='public')
    
    total_stats = {
        'users': 0,
        'patients': 0,
        'professionals': 0,
        'admins': 0,
        'appointments': 0,
        'specializations': 0
    }
    
    # Poblar cada clínica
    for clinic in clinics:
        stats = populate_clinic(clinic)
        
        # Sumar estadísticas globales
        for key in total_stats:
            total_stats[key] += stats.get(key, 0)
    
    # Resumen final
    print(f"\n📊 ESTADÍSTICAS GLOBALES:")
    print("=" * 30)
    print(f"🏥 Clínicas pobladas: {clinics.count()}")
    print(f"👥 Total usuarios: {total_stats['users']}")
    print(f"   - Pacientes: {total_stats['patients']}")
    print(f"   - Profesionales: {total_stats['professionals']}")
    print(f"   - Administradores: {total_stats['admins']}")
    print(f"📅 Total citas: {total_stats['appointments']}")
    print(f"🎓 Especializaciones: {total_stats['specializations']}")
    
    print(f"\n🔑 CREDENCIALES:")
    print(f"   👑 Admin (todas las clínicas): admin@gmail.com / admin")
    print(f"   👥 Pacientes: [nombre].[apellido].[clinica]@paciente.com / paciente123")
    print(f"   👨‍⚕️ Profesionales: dr.[nombre].[apellido].[clinica]@psicologo.com / psicologo123")
    
    print(f"\n🔗 URLs VERIFICACIÓN:")
    print(f"   🌐 Admin Global: http://localhost:8000/admin/")
    print(f"   🏥 Bienestar: http://bienestar.localhost:8000/admin/")
    print(f"   🏥 Mindcare: http://mindcare.localhost:8000/admin/")
    
    print(f"\n✅ ¡REPOBLACIÓN COMPLETADA!")
    print(f"   Sistema listo con datos realistas y funcionales")

if __name__ == "__main__":
    main()