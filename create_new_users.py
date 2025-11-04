#!/usr/bin/env python
"""
Script para crear un ADMIN, un PACIENTE y un PSICÓLOGO
en la clínica 'bienestar'.
"""

import os
import django
from datetime import datetime, time, timedelta
from decimal import Decimal
from django.db import transaction

# 1. Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

# 2. Importar modelos y utilidades clave
from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context
from apps.tenants.models import Clinic
from apps.users.models import PatientProfile
from apps.professionals.models import ProfessionalProfile, Specialization, WorkingHours
from apps.appointments.models import PsychologistAvailability

User = get_user_model()
TENANT_SCHEMA = 'bienestar'
DEFAULT_PASSWORD = 'password456'


def create_user_for_tenant():
    print(f"\n🚀 Iniciando creación de usuarios en la clínica: {TENANT_SCHEMA.upper()}")
    
    try:
        clinic = Clinic.objects.get(schema_name=TENANT_SCHEMA)
    except Clinic.DoesNotExist:
        print(f"❌ Error: La clínica '{TENANT_SCHEMA}' no existe.")
        return

    # Usamos el contexto del esquema para asegurar que las operaciones se hagan en la BD correcta.
    with schema_context(TENANT_SCHEMA):
        print(f"   Conectado al esquema de {clinic.name}")

        try:
            # --- 1. Crear Administrador ---
            print("\n--- 1. Creando Administrador (Admin) ---")
            admin_user = User.objects.create_user(
                email='nuevo.admin@bienestar.com',
                password=DEFAULT_PASSWORD,
                first_name='Admin',
                last_name='Prueba',
                user_type='admin',
                is_staff=True,
                is_superuser=False,
                ci='10000000',
                date_of_birth=datetime(1990, 5, 15).date(),
            )
            print(f"   ✅ Admin creado: {admin_user.email} / {DEFAULT_PASSWORD}")
            
            # --- 2. Crear Paciente ---
            print("\n--- 2. Creando Paciente ---")
            patient_user = User.objects.create_user(
                email='nuevo.paciente@test.com',
                password=DEFAULT_PASSWORD,
                first_name='Nuevo',
                last_name='Paciente',
                user_type='patient',
                ci='20000000',
                date_of_birth=datetime(1995, 1, 1).date(),
                phone='77777777',
            )
            # Crear perfil de paciente (PatientProfile)
            PatientProfile.objects.create(
                user=patient_user,
                emergency_contact_name='Contacto Paciente',
                emergency_contact_phone='77777778',
                emergency_contact_relationship='Amigo',
                profile_completed=True
            )
            print(f"   ✅ Paciente creado: {patient_user.email} / {DEFAULT_PASSWORD}")

            # --- 3. Crear Psicólogo (Profesional) ---
            print("\n--- 3. Creando Psicólogo (Professional) ---")
            prof_user = User.objects.create_user(
                email='nuevo.psicologo@bienestar.com',
                password=DEFAULT_PASSWORD,
                first_name='Dr.',
                last_name='Creativo',
                user_type='professional',
                ci='30000000',
                date_of_birth=datetime(1985, 10, 20).date(),
                phone='88888888',
            )
            
            # Obtener una especialización para el perfil
            specialization = Specialization.objects.first()
            if not specialization:
                print("   ⚠️ ADVERTENCIA: No se encontró especialización. Ejecuta 'create_specializations' primero.")
                return

            # Crear perfil profesional (ProfessionalProfile)
            profile = ProfessionalProfile.objects.create(
                user=prof_user,
                license_number='LIC-NUEVO-001',
                bio='Psicólogo especializado en explorar la creatividad.',
                education='Universidad de la Inspiración',
                experience_years=10,
                consultation_fee=Decimal('250.00'),
                profile_completed=True
            )
            profile.specializations.add(specialization)
            
            # Crear disponibilidad (WorkingHours y PsychologistAvailability)
            WorkingHours.objects.create(
                professional=profile,
                day_of_week=1, # Martes
                start_time=time(9, 0),
                end_time=time(17, 0)
            )
            PsychologistAvailability.objects.create(
                psychologist=prof_user,
                weekday=1, # Martes
                start_time=time(9, 0),
                end_time=time(17, 0)
            )
            print(f"   ✅ Psicólogo creado: {prof_user.email} / {DEFAULT_PASSWORD}")
            print("   (Perfil y disponibilidad creados)")

            print("\n🎉 ¡Todos los usuarios de prueba han sido creados exitosamente!")

        except Exception as e:
            print(f"\n❌ ERROR CRÍTICO durante la creación: {e}")
            print(f"   Asegúrate de que la clínica '{TENANT_SCHEMA}' exista y las migraciones se hayan aplicado.")
            
if __name__ == '__main__':
    create_user_for_tenant()