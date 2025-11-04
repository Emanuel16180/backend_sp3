#!/usr/bin/env python
"""
Script para listar TODOS los usuarios admin del sistema
Ejecutar en Render Shell: python list_all_admins.py
"""

import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django_tenants.utils import schema_context
from apps.tenants.models import Clinic

User = get_user_model()

def list_global_admins():
    """Listar administradores en el esquema público (global)"""
    print("\n" + "="*70)
    print("🌐 ADMINISTRADORES GLOBALES (Esquema: public)")
    print("="*70)
    
    # Cambiar al esquema público
    with connection.cursor() as cursor:
        cursor.execute("SET search_path TO public")
    
    # Buscar todos los superusuarios
    global_admins = User.objects.filter(is_superuser=True)
    
    if global_admins.exists():
        for admin in global_admins:
            print(f"\n👤 Usuario: {admin.username}")
            print(f"   📧 Email: {admin.email}")
            print(f"   👔 Nombre: {admin.get_full_name() or 'Sin nombre'}")
            print(f"   🔑 Superuser: {'✅ SÍ' if admin.is_superuser else '❌ NO'}")
            print(f"   📅 Último login: {admin.last_login or 'Nunca'}")
            print(f"   ⚠️  NOTA: Contraseña hasheada, necesitas resetearla si no la recuerdas")
    else:
        print("\n⚠️  NO HAY ADMINISTRADORES GLOBALES")
        print("   Necesitas crear uno con: python manage.py createsuperuser")
    
    # También buscar usuarios admin (no superuser pero con is_staff=True)
    staff_users = User.objects.filter(is_staff=True, is_superuser=False)
    if staff_users.exists():
        print("\n👥 USUARIOS STAFF (NO SUPERUSER):")
        for user in staff_users:
            print(f"   - {user.email} ({user.get_full_name()})")

def list_tenant_admins():
    """Listar administradores de cada clínica (tenant)"""
    print("\n" + "="*70)
    print("🏥 ADMINISTRADORES POR CLÍNICA")
    print("="*70)
    
    clinics = Clinic.objects.exclude(schema_name='public').all()
    
    for clinic in clinics:
        print(f"\n{'─'*70}")
        print(f"🏥 CLÍNICA: {clinic.name.upper()} (Schema: {clinic.schema_name})")
        print(f"{'─'*70}")
        
        with schema_context(clinic.schema_name):
            # Buscar admins de la clínica
            clinic_admins = User.objects.filter(user_type='admin')
            
            if clinic_admins.exists():
                for admin in clinic_admins:
                    print(f"\n👤 Usuario: {admin.username}")
                    print(f"   📧 Email: {admin.email}")
                    print(f"   👔 Nombre: {admin.get_full_name()}")
                    print(f"   🏷️  Tipo: {admin.user_type}")
                    print(f"   📞 Teléfono: {admin.phone or 'No registrado'}")
                    print(f"   📅 Creado: {admin.date_joined}")
                    print(f"   🔑 Staff: {'✅ SÍ' if admin.is_staff else '❌ NO'}")
                    
                    # Intentar mostrar la contraseña si es de los datos demo
                    if '@bienestar.com' in admin.email or '@mindcare.com' in admin.email:
                        print(f"   🔓 Contraseña: admin123 (datos demo)")
            else:
                print("\n⚠️  NO HAY ADMINISTRADORES EN ESTA CLÍNICA")
            
            # Mostrar también profesionales y pacientes (resumen)
            total_professionals = User.objects.filter(user_type='professional').count()
            total_patients = User.objects.filter(user_type='patient').count()
            total_users = User.objects.count()
            
            print(f"\n📊 RESUMEN DE USUARIOS:")
            print(f"   👥 Total usuarios: {total_users}")
            print(f"   👨‍⚕️ Profesionales: {total_professionals}")
            print(f"   🧑‍🤝‍🧑 Pacientes: {total_patients}")
            print(f"   🔧 Admins: {clinic_admins.count()}")

def main():
    print("\n🔍 LISTADO COMPLETO DE ADMINISTRADORES")
    print("📅 Fecha: 2025-10-21")
    
    # Listar admins globales
    list_global_admins()
    
    # Listar admins por clínica
    list_tenant_admins()
    
    print("\n" + "="*70)
    print("✅ LISTADO COMPLETADO")
    print("="*70)
    
    print("\n📝 CREDENCIALES CONOCIDAS (de populate_demo_data.py):")
    print("\n🏥 BIENESTAR:")
    print("   Admin: admin@bienestar.com / admin123")
    print("\n🏥 MINDCARE:")
    print("   Admin: admin@mindcare.com / admin123")
    
    print("\n⚠️  IMPORTANTE:")
    print("   - Si necesitas crear un superusuario global, usa:")
    print("     python manage.py createsuperuser")
    print("   - Para resetear contraseña de un usuario:")
    print("     python manage.py changepassword <email>")
    print()

if __name__ == '__main__':
    main()
