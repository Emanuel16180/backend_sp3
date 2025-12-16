"""
Script para crear usuarios adicionales en producción
Ejecutar desde Render Shell o localmente con DATABASE_URL de producción
"""

import os
import django
from django.db import connection

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.professionals.models import Professional, Specialty
from django_tenants.utils import schema_context

User = get_user_model()

def create_users_bienestar():
    """Crear usuarios en el tenant bienestar"""
    
    with schema_context('bienestar'):
        print("\n" + "="*60)
        print("🏥 CREANDO USUARIOS EN BIENESTAR")
        print("="*60)
        
        users_created = 0
        users_existing = 0
        
        # 1. Administrador
        email = "nuevo.admin@bienestar.com"
        if not User.objects.filter(email=email).exists():
            admin = User.objects.create_user(
                email=email,
                password="password456",
                first_name="Nuevo",
                last_name="Admin",
                role="admin",
                is_staff=True,
                is_active=True
            )
            print(f"✅ Admin creado: {email}")
            users_created += 1
        else:
            print(f"⚠️  Admin ya existe: {email}")
            users_existing += 1
        
        # 2. Paciente
        email = "nuevo.paciente@test.com"
        if not User.objects.filter(email=email).exists():
            patient = User.objects.create_user(
                email=email,
                password="password456",
                first_name="Nuevo",
                last_name="Paciente",
                role="patient",
                is_active=True
            )
            print(f"✅ Paciente creado: {email}")
            users_created += 1
        else:
            print(f"⚠️  Paciente ya existe: {email}")
            users_existing += 1
        
        # 3. Psicólogo
        email = "nuevo.psicologo@bienestar.com"
        if not User.objects.filter(email=email).exists():
            psicologo = User.objects.create_user(
                email=email,
                password="password456",
                first_name="Nuevo",
                last_name="Psicólogo",
                role="professional",
                is_active=True
            )
            
            # Obtener o crear especialidad de Psicología
            psicologia, _ = Specialty.objects.get_or_create(
                name="Psicología Clínica",
                defaults={'description': 'Especialidad en psicología clínica'}
            )
            
            # Crear perfil profesional
            Professional.objects.create(
                user=psicologo,
                specialty=psicologia,
                license_number=f"PSI-{psicologo.id:04d}",
                bio="Psicólogo clínico especializado en terapia cognitivo-conductual"
            )
            print(f"✅ Psicólogo creado: {email}")
            users_created += 1
        else:
            print(f"⚠️  Psicólogo ya existe: {email}")
            users_existing += 1
        
        # 4. Psiquiatra
        email = "dr.valverde@bienestar.com"
        if not User.objects.filter(email=email).exists():
            psiquiatra = User.objects.create_user(
                email=email,
                password="demo123",
                first_name="Dr. Valverde",
                last_name="",
                role="professional",
                is_active=True
            )
            
            # Obtener o crear especialidad de Psiquiatría
            psiquiatria, _ = Specialty.objects.get_or_create(
                name="Psiquiatría",
                defaults={'description': 'Especialidad médica en psiquiatría'}
            )
            
            # Crear perfil profesional
            Professional.objects.create(
                user=psiquiatra,
                specialty=psiquiatria,
                license_number=f"PSQ-{psiquiatra.id:04d}",
                bio="Psiquiatra especializado en tratamiento farmacológico y terapia"
            )
            print(f"✅ Psiquiatra creado: {email}")
            users_created += 1
        else:
            print(f"⚠️  Psiquiatra ya existe: {email}")
            users_existing += 1
        
        # 5-7. Pacientes adicionales
        pacientes = [
            ("ana.torres@example.com", "Ana", "Torres"),
            ("mario.ruiz@example.com", "Mario", "Ruiz"),
            ("sofia.vega@example.com", "Sofía", "Vega")
        ]
        
        for email, first_name, last_name in pacientes:
            if not User.objects.filter(email=email).exists():
                User.objects.create_user(
                    email=email,
                    password="demo123",
                    first_name=first_name,
                    last_name=last_name,
                    role="patient",
                    is_active=True
                )
                print(f"✅ Paciente creado: {email}")
                users_created += 1
            else:
                print(f"⚠️  Paciente ya existe: {email}")
                users_existing += 1
        
        print(f"\n📊 Total bienestar: {users_created} nuevos, {users_existing} existentes")
        return users_created, users_existing

def main():
    print("\n" + "="*60)
    print("👥 CREACIÓN DE USUARIOS ADICIONALES - PRODUCCIÓN")
    print("="*60)
    print(f"🗄️  Base de datos: {connection.settings_dict['NAME']}")
    print(f"🔧 Host: {connection.settings_dict['HOST']}")
    print("="*60)
    
    try:
        total_created, total_existing = create_users_bienestar()
        
        print("\n" + "="*60)
        print("✅ PROCESO COMPLETADO")
        print("="*60)
        print(f"📊 Total usuarios creados: {total_created}")
        print(f"⚠️  Total usuarios existentes: {total_existing}")
        
        if total_created > 0:
            print("\n🔐 CREDENCIALES CREADAS:")
            print("-" * 60)
            print("Grupo 1 (password456):")
            print("  - nuevo.admin@bienestar.com / password456")
            print("  - nuevo.paciente@test.com / password456")
            print("  - nuevo.psicologo@bienestar.com / password456")
            print("\nGrupo 2 (demo123):")
            print("  - dr.valverde@bienestar.com / demo123")
            print("  - ana.torres@example.com / demo123")
            print("  - mario.ruiz@example.com / demo123")
            print("  - sofia.vega@example.com / demo123")
            print("-" * 60)
        
    except Exception as e:
        print(f"\n❌ Error durante la creación: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
