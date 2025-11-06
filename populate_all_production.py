#!/usr/bin/env python
"""
Script para poblar AMBOS tenants (bienestar y mindcare) con usuarios y datos completos.
⚠️ SOLO AÑADE datos, NO elimina nada existente.
"""

import os
import django
from datetime import datetime, time, timedelta
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context
from apps.users.models import PatientProfile
from apps.professionals.models import ProfessionalProfile, Specialization, WorkingHours
from apps.appointments.models import PsychologistAvailability

User = get_user_model()
DEFAULT_PASSWORD = 'demo123'
ADMIN_PASSWORD = 'admin123'

print("=" * 80)
print("🚀 POBLACIÓN COMPLETA DE DATOS PARA PRODUCCIÓN")
print("=" * 80)

def create_data_for_tenant(tenant_name):
    """Crear usuarios y datos completos para un tenant"""
    print(f"\n{'='*80}")
    print(f"🏢 TENANT: {tenant_name.upper()}")
    print(f"{'='*80}")
    
    with schema_context(tenant_name):
        created_count = 0
        
        # 1. ADMIN
        print(f"\n👤 Creando Admin...")
        if not User.objects.filter(email=f'admin@{tenant_name}.com').exists():
            admin = User.objects.create_user(
                email=f'admin@{tenant_name}.com',
                password=ADMIN_PASSWORD,
                first_name='Admin',
                last_name=tenant_name.capitalize(),
                user_type='admin',
                is_staff=True,
                is_superuser=True,
                ci='10000001',
                date_of_birth=datetime(1985, 1, 1).date(),
            )
            print(f'  ✅ Admin: admin@{tenant_name}.com / {ADMIN_PASSWORD}')
            created_count += 1
        else:
            print(f'  ⏭️  Admin ya existe')
        
        # 2. ESPECIALIDADES
        print(f"\n🏥 Creando Especialidades...")
        specializations = [
            'Psicología Clínica',
            'Terapia Familiar',
            'Psicología Infantil',
            'Terapia de Pareja'
        ]
        
        for spec_name in specializations:
            spec, created = Specialization.objects.get_or_create(
                name=spec_name,
                defaults={'description': f'Especialidad en {spec_name}'}
            )
            if created:
                print(f'  ✅ {spec_name}')
        
        # 3. PROFESIONALES
        professionals_data = [
            {
                'email': f'dra.martinez@{tenant_name}.com',
                'first_name': 'Laura',
                'last_name': 'Martínez',
                'license': 'PSI-12345',
                'fee': '200.00'
            },
            {
                'email': f'dr.garcia@{tenant_name}.com',
                'first_name': 'Carlos',
                'last_name': 'García',
                'license': 'PSI-54321',
                'fee': '250.00'
            }
        ]
        
        print(f"\n👨‍⚕️ Creando Profesionales...")
        for prof_data in professionals_data:
            if not User.objects.filter(email=prof_data['email']).exists():
                user = User.objects.create_user(
                    email=prof_data['email'],
                    password=DEFAULT_PASSWORD,
                    first_name=prof_data['first_name'],
                    last_name=prof_data['last_name'],
                    user_type='professional',
                    ci=prof_data['license'][-5:],
                    date_of_birth=datetime(1985, 5, 10).date(),
                    phone='77700000',
                )
                
                # Perfil profesional
                spec = Specialization.objects.first()
                profile = ProfessionalProfile.objects.create(
                    user=user,
                    license_number=prof_data['license'],
                    bio=f'{prof_data["first_name"]} {prof_data["last_name"]} - Profesional certificado',
                    education='Universidad Nacional',
                    experience_years=8,
                    consultation_fee=Decimal(prof_data['fee']),
                    profile_completed=True
                )
                if spec:
                    profile.specializations.add(spec)
                
                # Horarios de trabajo (Lunes a Viernes, 9am-5pm)
                for day in range(1, 6):  # 1=Lunes, 5=Viernes
                    WorkingHours.objects.create(
                        professional=profile,
                        day_of_week=day,
                        start_time=time(9, 0),
                        end_time=time(17, 0)
                    )
                    PsychologistAvailability.objects.create(
                        psychologist=user,
                        weekday=day,
                        start_time=time(9, 0),
                        end_time=time(17, 0)
                    )
                
                print(f'  ✅ {prof_data["email"]} / {DEFAULT_PASSWORD}')
                created_count += 1
            else:
                print(f'  ⏭️  {prof_data["email"]} ya existe')
        
        # 4. PACIENTES
        patients_data = [
            {'email': f'juan.perez@example.com', 'first_name': 'Juan', 'last_name': 'Pérez', 'ci': '20001'},
            {'email': f'maria.lopez@example.com', 'first_name': 'María', 'last_name': 'López', 'ci': '20002'},
            {'email': f'carlos.ruiz@example.com', 'first_name': 'Carlos', 'last_name': 'Ruiz', 'ci': '20003'},
        ]
        
        print(f"\n🧑 Creando Pacientes...")
        for patient_data in patients_data:
            if not User.objects.filter(email=patient_data['email']).exists():
                user = User.objects.create_user(
                    email=patient_data['email'],
                    password=DEFAULT_PASSWORD,
                    first_name=patient_data['first_name'],
                    last_name=patient_data['last_name'],
                    user_type='patient',
                    ci=patient_data['ci'],
                    date_of_birth=datetime(1995, 3, 15).date(),
                    phone='70000000',
                )
                
                PatientProfile.objects.create(
                    user=user,
                    emergency_contact_name='Contacto Emergencia',
                    emergency_contact_phone='70000001',
                    emergency_contact_relationship='Familiar',
                    profile_completed=True
                )
                
                print(f'  ✅ {patient_data["email"]} / {DEFAULT_PASSWORD}')
                created_count += 1
            else:
                print(f'  ⏭️  {patient_data["email"]} ya existe')
        
        print(f"\n📊 Total creado en {tenant_name}: {created_count} usuarios")
        return created_count

# EJECUTAR PARA AMBOS TENANTS
try:
    total_bienestar = create_data_for_tenant('bienestar')
    total_mindcare = create_data_for_tenant('mindcare')
    
    print("\n" + "=" * 80)
    print("✅ POBLACIÓN COMPLETADA EXITOSAMENTE")
    print("=" * 80)
    print(f"\n📊 Resumen:")
    print(f"   • Bienestar: {total_bienestar} usuarios creados")
    print(f"   • Mindcare: {total_mindcare} usuarios creados")
    print("=" * 80)
    print("\n🔑 CREDENCIALES DE ACCESO:")
    print("=" * 80)
    
    for tenant in ['bienestar', 'mindcare']:
        print(f"\n{tenant.upper()}:")
        print(f"  Admin:       admin@{tenant}.com / {ADMIN_PASSWORD}")
        print(f"  Profesional: dra.martinez@{tenant}.com / {DEFAULT_PASSWORD}")
        print(f"  Paciente:    juan.perez@example.com / {DEFAULT_PASSWORD}")
    
    print("=" * 80)
    print("\n🎉 ¡Listo! Ahora puedes probar el login desde el frontend")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
