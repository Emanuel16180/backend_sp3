"""
Script COMPLETO para poblar TODOS los datos de demostración
Incluye: Usuarios, Profesionales, Pacientes, Citas, MoodJournal, Objetivos, Tareas
"""

import os
import django
from datetime import datetime, timedelta, time, date
from decimal import Decimal
from random import choice, randint

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context
from apps.tenants.models import Clinic
from apps.users.models import CustomUser, PatientProfile
from apps.professionals.models import ProfessionalProfile, Specialization, WorkingHours
from apps.appointments.models import Appointment
from apps.clinical_history.models import MoodJournal, Objective, Task

User = get_user_model()

def populate_tenant(tenant_name, config):
    """Poblar un tenant completo con todos los datos"""
    
    try:
        clinic = Clinic.objects.get(schema_name=tenant_name)
    except Clinic.DoesNotExist:
        print(f"❌ Tenant '{tenant_name}' no existe")
        return
    
    with schema_context(tenant_name):
        print(f"\n{'='*60}")
        print(f"🏥 POBLANDO: {clinic.name.upper()}")
        print(f"{'='*60}")
        
        # 1. ESPECIALIDADES
        print("\n📚 1. Creando especialidades...")
        specializations = {}
        for spec in config['specialties']:
            obj, created = Specialization.objects.get_or_create(
                name=spec['name'],
                defaults={'description': spec['description']}
            )
            specializations[spec['name']] = obj
            print(f"  {'✅' if created else 'ℹ️'} {obj.name}")
        
        # 2. PROFESIONALES
        print("\n👨‍⚕️ 2. Creando profesionales...")
        professionals = []
        for prof in config['professionals']:
            user, u_created = CustomUser.objects.get_or_create(
                email=prof['email'],
                defaults={
                    'username': prof['email'].split('@')[0],
                    'first_name': prof['first_name'],
                    'last_name': prof['last_name'],
                    'phone': prof['phone'],
                    'user_type': 'professional',
                }
            )
            if u_created:
                user.set_password('demo123')
                user.save()
            
            profile, p_created = ProfessionalProfile.objects.get_or_create(
                user=user,
                defaults={
                    'license_number': prof['license'],
                    'bio': f"Especialista en {prof['specialty']} con 5+ años de experiencia",
                    'education': 'Universidad Complutense de Madrid',
                    'experience_years': randint(5, 15),
                    'consultation_fee': Decimal(str(randint(40, 80)) + '.00'),
                    'is_active': True,
                    'profile_completed': True,
                    'is_verified': True,
                    'accepts_online_sessions': True,
                }
            )
            
            if not p_created:
                profile.is_active = True
                profile.profile_completed = True
                profile.is_verified = True
                profile.save()
            
            # Asignar especialización
            spec = specializations[prof['specialty']]
            if spec not in profile.specializations.all():
                profile.specializations.add(spec)
            
            professionals.append(profile)
            print(f"  {'✅' if p_created else 'ℹ️'} {user.get_full_name()} - {prof['specialty']}")
            
            # Horarios
            for day in range(5):
                WorkingHours.objects.get_or_create(
                    professional=profile,
                    day_of_week=day,
                    defaults={
                        'start_time': time(9, 0),
                        'end_time': time(18, 0),
                        'is_active': True,
                    }
                )
        
        # 3. PACIENTES
        print("\n🧑‍🤝‍🧑 3. Creando pacientes...")
        patients = []
        for pat in config['patients']:
            user, u_created = CustomUser.objects.get_or_create(
                email=pat['email'],
                defaults={
                    'username': pat['email'].split('@')[0],
                    'first_name': pat['first_name'],
                    'last_name': pat['last_name'],
                    'phone': pat['phone'],
                    'user_type': 'patient',
                    'date_of_birth': date.today() - timedelta(days=365*randint(25, 50)),
                    'address': f"Calle {choice(['Mayor', 'Gran Via', 'Alcala', 'Serrano'])} {randint(1, 100)}",
                    'gender': choice(['male', 'female', 'other']),
                }
            )
            if u_created:
                user.set_password('demo123')
                user.save()
            
            PatientProfile.objects.get_or_create(
                user=user,
                defaults={
                    'emergency_contact_phone': pat['phone'],
                    'emergency_contact_name': f"Contacto de {user.first_name}",
                    'emergency_contact_relationship': choice(['Madre', 'Padre', 'Hermano/a', 'Pareja']),
                }
            )
            
            patients.append(user)
            print(f"  {'✅' if u_created else 'ℹ️'} {user.get_full_name()}")
        
        # 4. MOOD JOURNAL (últimos 7 días para cada paciente)
        print("\n😊 4. Creando registros de Mood Journal...")
        moods = ['feliz', 'triste', 'ansioso', 'enojado', 'neutral', 'cansado']
        mood_count = 0
        
        for patient in patients:
            for days_ago in range(7):
                journal_date = date.today() - timedelta(days=days_ago)
                mood = choice(moods)
                
                _, created = MoodJournal.objects.get_or_create(
                    patient=patient,
                    date=journal_date,
                    defaults={
                        'mood': mood,
                        'notes': f"Registro de prueba para {journal_date.strftime('%d/%m/%Y')}. Me sentí {mood}.",
                    }
                )
                if created:
                    mood_count += 1
        
        print(f"  ✅ {mood_count} registros de ánimo creados")
        
        # 5. CITAS
        print("\n📅 5. Creando citas...")
        appointment_count = 0
        statuses = ['pending', 'confirmed', 'completed', 'cancelled']
        types = ['online', 'in_person']
        
        for i, patient in enumerate(patients):
            prof = professionals[i % len(professionals)]
            
            # Crear 3-5 citas por paciente en diferentes fechas
            for j in range(randint(3, 5)):
                days_offset = randint(-30, 30)  # Citas pasadas y futuras
                appt_date = date.today() + timedelta(days=days_offset)
                appt_time = time(randint(9, 17), choice([0, 30]))
                
                # Status según la fecha
                if days_offset < -7:
                    status = 'completed'
                elif days_offset < 0:
                    status = choice(['completed', 'cancelled'])
                else:
                    status = choice(['pending', 'confirmed'])
                
                _, created = Appointment.objects.get_or_create(
                    patient=patient,
                    psychologist=prof.user,
                    appointment_date=appt_date,
                    start_time=appt_time,
                    defaults={
                        'status': status,
                        'end_time': (datetime.combine(date.today(), appt_time) + timedelta(hours=1)).time(),
                        'reason_for_visit': choice([
                            'Consulta inicial',
                            'Seguimiento de terapia',
                            'Manejo de ansiedad',
                            'Control de tratamiento',
                            'Sesión de apoyo',
                        ]),
                        'consultation_fee': prof.consultation_fee,
                        'appointment_type': choice(types),
                        'notes': f'Cita de ejemplo - {status}' if randint(0, 1) else '',
                    }
                )
                if created:
                    appointment_count += 1
        
        print(f"  ✅ {appointment_count} citas creadas")
        
        # 6. OBJETIVOS Y TAREAS
        print("\n🎯 6. Creando objetivos y tareas...")
        objective_count = 0
        task_count = 0
        
        for patient in patients[:3]:  # Solo primeros 3 pacientes
            prof = professionals[0]  # Primer profesional
            
            # Crear 2 objetivos por paciente
            for obj_num in range(1, 3):
                obj, created = Objective.objects.get_or_create(
                    patient=patient,
                    psychologist=prof.user,
                    title=f"Objetivo {obj_num} para {patient.first_name}",
                    defaults={
                        'description': f"Descripción detallada del objetivo {obj_num}. Este es un objetivo terapéutico diseñado específicamente.",
                        'status': choice(['active', 'completed']),
                    }
                )
                
                if created:
                    objective_count += 1
                    
                    # Crear 3-5 tareas por objetivo
                    for task_num in range(1, randint(3, 6)):
                        task, t_created = Task.objects.get_or_create(
                            objective=obj,
                            title=f"Tarea {task_num} del Objetivo {obj_num}",
                            defaults={
                                'recurrence': choice(['once', 'daily', 'weekly']),
                            }
                        )
                        if t_created:
                            task_count += 1
        
        print(f"  ✅ {objective_count} objetivos creados")
        print(f"  ✅ {task_count} tareas creadas")
        
        # RESUMEN FINAL
        print(f"\n{'='*60}")
        print(f"📊 RESUMEN FINAL - {clinic.name}")
        print(f"{'='*60}")
        print(f"  👥 Usuarios totales: {CustomUser.objects.count()}")
        print(f"  👨‍⚕️ Profesionales: {ProfessionalProfile.objects.filter(is_active=True, profile_completed=True).count()}")
        print(f"  🧑‍🤝‍🧑 Pacientes: {CustomUser.objects.filter(user_type='patient').count()}")
        print(f"  📚 Especialidades: {Specialization.objects.count()}")
        print(f"  📅 Citas: {Appointment.objects.count()}")
        print(f"  ⏰ Horarios: {WorkingHours.objects.count()}")
        print(f"  😊 Mood Journals: {MoodJournal.objects.count()}")
        print(f"  🎯 Objetivos: {Objective.objects.count()}")
        print(f"  ✅ Tareas: {Task.objects.count()}")
        print(f"{'='*60}")


def main():
    print("\n" + "🚀" * 30)
    print("POBLACIÓN COMPLETA DE DATOS DE DEMOSTRACIÓN")
    print("🚀" * 30)
    
    # Configuración para ambos tenants
    BIENESTAR_CONFIG = {
        'specialties': [
            {'name': 'Psicologia Clinica', 'description': 'Tratamiento de trastornos mentales y emocionales'},
            {'name': 'Psicologia Infantil', 'description': 'Especialización en niños y adolescentes'},
            {'name': 'Terapia de Pareja', 'description': 'Resolución de conflictos en relaciones'},
            {'name': 'Psicologia Deportiva', 'description': 'Apoyo psicológico para deportistas'},
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
    }
    
    MINDCARE_CONFIG = {
        'specialties': [
            {'name': 'Psicologia Cognitivo-Conductual', 'description': 'Tratamiento basado en pensamientos y conductas'},
            {'name': 'Neuropsicologia', 'description': 'Evaluación y rehabilitación cognitiva'},
            {'name': 'Psicologia Organizacional', 'description': 'Salud mental en el trabajo'},
            {'name': 'Mindfulness y Bienestar', 'description': 'Técnicas de atención plena'},
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
    
    # Poblar ambos tenants
    populate_tenant('bienestar', BIENESTAR_CONFIG)
    populate_tenant('mindcare', MINDCARE_CONFIG)
    
    # Credenciales finales
    print("\n" + "🔑" * 30)
    print("CREDENCIALES DE ACCESO")
    print("🔑" * 30)
    print("\n🏥 BIENESTAR:")
    print("  Admin: admin@bienestar.com / admin123")
    print("  Profesionales:")
    print("    - dra.martinez@bienestar.com / demo123")
    print("    - dr.garcia@bienestar.com / demo123")
    print("    - dra.lopez@bienestar.com / demo123")
    print("  Pacientes:")
    print("    - juan.perez@example.com / demo123")
    print("    - maria.gomez@example.com / demo123")
    print("    - pedro.sanchez@example.com / demo123")
    
    print("\n🏥 MINDCARE:")
    print("  Admin: admin@mindcare.com / admin123")
    print("  Profesionales:")
    print("    - dra.torres@mindcare.com / demo123")
    print("    - dr.ramirez@mindcare.com / demo123")
    print("    - dra.morales@mindcare.com / demo123")
    print("  Pacientes:")
    print("    - carlos.ruiz@example.com / demo123")
    print("    - elena.castro@example.com / demo123")
    print("    - javier.ortiz@example.com / demo123")
    
    print("\n" + "🎉" * 30)
    print("¡POBLACIÓN COMPLETA EXITOSA!")
    print("🎉" * 30 + "\n")


if __name__ == '__main__':
    main()
