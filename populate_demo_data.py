"""
Script para poblar datos de demostracion en ambos tenants (bienestar y mindcare)
Ejecutar en Render Shell: python populate_demo_data.py
"""

import os
import django
from datetime import datetime, timedelta, time
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context
from apps.tenants.models import Clinic
from apps.users.models import CustomUser, PatientProfile
from apps.professionals.models import ProfessionalProfile, Specialization, WorkingHours
from apps.appointments.models import Appointment

User = get_user_model()

# Datos de demostracion
DEMO_DATA = {
    'bienestar': {
        'specialties': [
            {'name': 'Psicologia Clinica', 'description': 'Tratamiento de trastornos mentales y emocionales'},
            {'name': 'Psicologia Infantil', 'description': 'Especializacion en ninos y adolescentes'},
            {'name': 'Terapia de Pareja', 'description': 'Resolucion de conflictos en relaciones'},
            {'name': 'Psicologia Deportiva', 'description': 'Apoyo psicologico para deportistas'},
        ],
        'professionals': [
            {
                'email': 'dra.martinez@bienestar.com',
                'first_name': 'Laura',
                'last_name': 'Martinez',
                'specialty': 'Psicologia Clinica',
                'license': 'PSI-2024-001',
                'phone': '+34 612 345 678',
            },
            {
                'email': 'dr.garcia@bienestar.com',
                'first_name': 'Carlos',
                'last_name': 'Garcia',
                'specialty': 'Psicologia Infantil',
                'license': 'PSI-2024-002',
                'phone': '+34 623 456 789',
            },
            {
                'email': 'dra.lopez@bienestar.com',
                'first_name': 'Ana',
                'last_name': 'Lopez',
                'specialty': 'Terapia de Pareja',
                'license': 'PSI-2024-003',
                'phone': '+34 634 567 890',
            },
        ],
        'patients': [
            {'email': 'juan.perez@example.com', 'first_name': 'Juan', 'last_name': 'Perez', 'phone': '+34 645 111 222'},
            {'email': 'maria.gomez@example.com', 'first_name': 'Maria', 'last_name': 'Gomez', 'phone': '+34 656 222 333'},
            {'email': 'pedro.sanchez@example.com', 'first_name': 'Pedro', 'last_name': 'Sanchez', 'phone': '+34 667 333 444'},
            {'email': 'lucia.fernandez@example.com', 'first_name': 'Lucia', 'last_name': 'Fernandez', 'phone': '+34 678 444 555'},
            {'email': 'diego.rodriguez@example.com', 'first_name': 'Diego', 'last_name': 'Rodriguez', 'phone': '+34 689 555 666'},
        ]
    },
    'mindcare': {
        'specialties': [
            {'name': 'Psicologia Cognitivo-Conductual', 'description': 'Tratamiento basado en pensamientos y conductas'},
            {'name': 'Neuropsicologia', 'description': 'Evaluacion y rehabilitacion cognitiva'},
            {'name': 'Psicologia Organizacional', 'description': 'Salud mental en el trabajo'},
            {'name': 'Mindfulness y Bienestar', 'description': 'Tecnicas de atencion plena'},
        ],
        'professionals': [
            {
                'email': 'dra.torres@mindcare.com',
                'first_name': 'Isabel',
                'last_name': 'Torres',
                'specialty': 'Psicologia Cognitivo-Conductual',
                'license': 'PSI-2024-101',
                'phone': '+34 611 987 654',
            },
            {
                'email': 'dr.ramirez@mindcare.com',
                'first_name': 'Miguel',
                'last_name': 'Ramirez',
                'specialty': 'Neuropsicologia',
                'license': 'PSI-2024-102',
                'phone': '+34 622 876 543',
            },
            {
                'email': 'dra.morales@mindcare.com',
                'first_name': 'Sofia',
                'last_name': 'Morales',
                'specialty': 'Mindfulness y Bienestar',
                'license': 'PSI-2024-103',
                'phone': '+34 633 765 432',
            },
        ],
        'patients': [
            {'email': 'carlos.ruiz@example.com', 'first_name': 'Carlos', 'last_name': 'Ruiz', 'phone': '+34 644 777 888'},
            {'email': 'elena.castro@example.com', 'first_name': 'Elena', 'last_name': 'Castro', 'phone': '+34 655 888 999'},
            {'email': 'javier.ortiz@example.com', 'first_name': 'Javier', 'last_name': 'Ortiz', 'phone': '+34 666 999 000'},
            {'email': 'carmen.silva@example.com', 'first_name': 'Carmen', 'last_name': 'Silva', 'phone': '+34 677 000 111'},
            {'email': 'roberto.vega@example.com', 'first_name': 'Roberto', 'last_name': 'Vega', 'phone': '+34 688 111 222'},
        ]
    }
}

def create_demo_data_for_tenant(tenant_name, data):
    """Crear datos de demostracion para un tenant especifico"""
    
    try:
        clinic = Clinic.objects.get(schema_name=tenant_name)
    except Clinic.DoesNotExist:
        print(f"X Tenant '{tenant_name}' no existe")
        return
    
    with schema_context(tenant_name):
        print(f"\n>> Poblando datos para: {clinic.name} (schema: {tenant_name})")
        
        # 1. Crear especialidades
        print("\n>> Creando especialidades...")
        specializations = {}
        for spec_data in data['specialties']:
            specialization, created = Specialization.objects.get_or_create(
                name=spec_data['name'],
                defaults={'description': spec_data['description']}
            )
            specializations[spec_data['name']] = specialization
            status = "[OK] Creada" if created else "[INFO] Ya existe"
            print(f"  {status}: {specialization.name}")
        
        # 2. Crear profesionales con usuarios
        print("\n>> Creando profesionales...")
        professionals = []
        for prof_data in data['professionals']:
            # Crear usuario
            user, created = CustomUser.objects.get_or_create(
                email=prof_data['email'],
                defaults={
                    'username': prof_data['email'].split('@')[0],
                    'first_name': prof_data['first_name'],
                    'last_name': prof_data['last_name'],
                    'phone': prof_data['phone'],
                    'user_type': 'professional',
                }
            )
            if created:
                user.set_password('demo123')
                user.save()
            
            # Crear profesional
            professional, created = ProfessionalProfile.objects.get_or_create(
                user=user,
                defaults={
                    'license_number': prof_data['license'],
                    'bio': f"Profesional especializado en {prof_data['specialty']}",
                    'education': 'Universidad de ejemplo',
                    'experience_years': 5,
                    'consultation_fee': Decimal('50.00'),
                }
            )
            
            # Asignar especialidad
            specialization = specializations[prof_data['specialty']]
            if specialization not in professional.specializations.all():
                professional.specializations.add(specialization)
            
            professionals.append(professional)
            status = "[OK] Creado" if created else "[INFO] Ya existe"
            print(f"  {status}: {professional.user.get_full_name()} - {prof_data['specialty']}")
            
            # Crear horarios (Lunes a Viernes, 9:00 - 18:00)
            for day in range(5):  # 0=Lunes, 4=Viernes
                schedule, created = WorkingHours.objects.get_or_create(
                    professional=professional,
                    day_of_week=day,
                    defaults={
                        'start_time': time(9, 0),
                        'end_time': time(18, 0),
                        'is_active': True,
                    }
                )
                if created:
                    print(f"    [OK] Horario creado: {schedule.get_day_of_week_display()} 9:00-18:00")
        
        # 3. Crear pacientes
        print("\n>> Creando pacientes...")
        patients = []
        for patient_data in data['patients']:
            # Crear usuario
            user, created = CustomUser.objects.get_or_create(
                email=patient_data['email'],
                defaults={
                    'username': patient_data['email'].split('@')[0],
                    'first_name': patient_data['first_name'],
                    'last_name': patient_data['last_name'],
                    'phone': patient_data['phone'],
                    'user_type': 'patient',
                    'date_of_birth': datetime.now().date() - timedelta(days=365*30),  # 30 anos
                    'address': 'Direccion de ejemplo',
                }
            )
            if created:
                user.set_password('demo123')
                user.save()
            
            # Crear perfil de paciente
            profile, profile_created = PatientProfile.objects.get_or_create(
                user=user,
                defaults={
                    'emergency_contact_phone': patient_data['phone'],
                    'emergency_contact_name': 'Contacto de emergencia',
                    'emergency_contact_relationship': 'Familiar',
                }
            )
            
            patients.append(user)
            status = "[OK] Creado" if created else "[INFO] Ya existe"
            print(f"  {status}: {user.get_full_name()}")
        
        # 4. Crear citas de ejemplo
        print("\n>> Creando citas de ejemplo...")
        appointment_statuses = [
            'pending',
            'confirmed',
            'completed',
        ]
        
        base_date = datetime.now()
        appointment_count = 0
        
        for i, patient in enumerate(patients[:3]):  # Solo 3 pacientes para no saturar
            professional = professionals[i % len(professionals)]
            
            # Crear 2-3 citas por paciente
            for j in range(2):
                appointment_date = base_date + timedelta(days=j*7)
                appointment_time = time(10 + j*2, 0)  # 10:00, 12:00, etc.
                
                appointment, created = Appointment.objects.get_or_create(
                    patient=patient,
                    psychologist=professional.user,
                    appointment_date=appointment_date.date(),
                    start_time=appointment_time,
                    defaults={
                        'status': appointment_statuses[j % len(appointment_statuses)],
                        'end_time': time(11 + j*2, 0),
                        'reason_for_visit': f'Cita de ejemplo - {appointment_statuses[j % len(appointment_statuses)]}',
                        'consultation_fee': Decimal('50.00'),
                        'appointment_type': 'in_person',
                    }
                )
                
                if created:
                    appointment_count += 1
                    print(f"  ✅ Cita: {patient.get_full_name()} con {professional.user.get_full_name()} - {appointment_date.strftime('%Y-%m-%d')} {appointment_time}")
        
        print(f"\n✅ Total de citas creadas: {appointment_count}")
        
        # Resumen
        print(f"\n📊 RESUMEN - {clinic.name}:")
        print(f"  👥 Usuarios: {CustomUser.objects.count()}")
        print(f"  👨‍⚕️ Profesionales: {ProfessionalProfile.objects.count()}")
        print(f"  🧑‍🤝‍🧑 Pacientes: {CustomUser.objects.filter(user_type='patient').count()}")
        print(f"  📚 Especialidades: {Specialization.objects.count()}")
        print(f"  📅 Citas: {Appointment.objects.count()}")
        print(f"  ⏰ Horarios: {WorkingHours.objects.count()}")

def main():
    print("ðŸš€ Iniciando poblaciÃ³n de datos de demostraciÃ³n...")
    print("=" * 60)
    
    # Poblar Bienestar
    create_demo_data_for_tenant('bienestar', DEMO_DATA['bienestar'])
    
    # Poblar Mindcare
    create_demo_data_for_tenant('mindcare', DEMO_DATA['mindcare'])
    
    print("\n" + "=" * 60)
    print("ðŸŽ‰ Â¡PoblaciÃ³n de datos completada!")
    print("\nðŸ“ CREDENCIALES DE ACCESO:")
    print("\nðŸ¥ BIENESTAR:")
    print("  Admin: admin@bienestar.com / admin123")
    print("  Profesionales:")
    print("    - dra.martinez@bienestar.com / demo123")
    print("    - dr.garcia@bienestar.com / demo123")
    print("    - dra.lopez@bienestar.com / demo123")
    print("  Pacientes:")
    print("    - juan.perez@example.com / demo123")
    print("    - maria.gomez@example.com / demo123")
    
    print("\nðŸ¥ MINDCARE:")
    print("  Admin: admin@mindcare.com / admin123")
    print("  Profesionales:")
    print("    - dra.torres@mindcare.com / demo123")
    print("    - dr.ramirez@mindcare.com / demo123")
    print("    - dra.morales@mindcare.com / demo123")
    print("  Pacientes:")
    print("    - carlos.ruiz@example.com / demo123")
    print("    - elena.castro@example.com / demo123")

if __name__ == '__main__':
    main()
