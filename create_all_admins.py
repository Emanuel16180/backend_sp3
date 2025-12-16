#!/usr/bin/env python
"""
Script para crear superusuario global y administradores de cada clínica
Ejecutar en Render Shell: python create_all_admins.py
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

def create_global_superuser():
    """Crear superusuario en el esquema público (global)"""
    print("\n" + "="*70)
    print("🌐 CREANDO SUPERUSUARIO GLOBAL (Esquema: public)")
    print("="*70)
    
    # Asegurarnos de estar en el esquema público
    with connection.cursor() as cursor:
        cursor.execute("SET search_path TO public")
    
    email = 'admin@psicoadmin.xyz'
    username = 'admin'
    password = 'admin123'
    
    # Verificar si ya existe
    if User.objects.filter(email=email).exists():
        print(f"\n⚠️  El superusuario ya existe: {email}")
        user = User.objects.get(email=email)
        print(f"   👤 Usuario: {user.username}")
        print(f"   📧 Email: {user.email}")
        print(f"   🔑 Superuser: {'✅ SÍ' if user.is_superuser else '❌ NO'}")
        return user
    
    # Crear superusuario
    try:
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
            first_name='Administrador',
            last_name='Global'
        )
        
        print(f"\n✅ SUPERUSUARIO CREADO EXITOSAMENTE")
        print(f"   👤 Usuario: {user.username}")
        print(f"   📧 Email: {user.email}")
        print(f"   🔑 Contraseña: {password}")
        print(f"   🔐 Superuser: ✅ SÍ")
        print(f"   🌐 URL: https://psico-admin.onrender.com/admin/")
        
        return user
        
    except Exception as e:
        print(f"\n❌ ERROR al crear superusuario: {e}")
        return None

def create_clinic_admin(clinic, admin_data):
    """Crear administrador para una clínica específica"""
    
    with schema_context(clinic.schema_name):
        email = admin_data['email']
        
        # Verificar si ya existe
        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            print(f"\n⚠️  Admin ya existe: {email}")
            print(f"   👤 Usuario: {user.username}")
            print(f"   🏷️  Tipo: {user.user_type}")
            
            # Actualizar si no es admin
            if user.user_type != 'admin':
                user.user_type = 'admin'
                user.is_staff = True
                user.save()
                print(f"   ✅ Actualizado a tipo 'admin'")
            
            return user
        
        # Crear nuevo administrador
        try:
            user = User.objects.create_user(
                username=admin_data['username'],
                email=email,
                password=admin_data['password'],
                first_name=admin_data['first_name'],
                last_name=admin_data['last_name'],
                user_type='admin',
                phone=admin_data.get('phone', '')
            )
            
            # Dar permisos de staff
            user.is_staff = True
            user.save()
            
            print(f"\n✅ ADMIN CREADO: {user.get_full_name()}")
            print(f"   📧 Email: {user.email}")
            print(f"   🔑 Contraseña: {admin_data['password']}")
            print(f"   🏷️  Tipo: {user.user_type}")
            print(f"   🔐 Staff: ✅ SÍ")
            
            return user
            
        except Exception as e:
            print(f"\n❌ ERROR al crear admin de {clinic.name}: {e}")
            return None

def create_all_clinic_admins():
    """Crear administradores para todas las clínicas"""
    print("\n" + "="*70)
    print("🏥 CREANDO ADMINISTRADORES DE CLÍNICAS")
    print("="*70)
    
    # Datos de los administradores
    admins_data = {
        'bienestar': {
            'username': 'admin.bienestar',
            'email': 'admin@bienestar.com',
            'password': 'admin123',
            'first_name': 'Admin',
            'last_name': 'Bienestar',
            'phone': '+34 600 111 222'
        },
        'mindcare': {
            'username': 'admin.mindcare',
            'email': 'admin@mindcare.com',
            'password': 'admin123',
            'first_name': 'Admin',
            'last_name': 'Mindcare',
            'phone': '+34 600 333 444'
        }
    }
    
    # Obtener todas las clínicas (excepto public)
    clinics = Clinic.objects.exclude(schema_name='public').all()
    
    created_admins = []
    
    for clinic in clinics:
        print(f"\n{'─'*70}")
        print(f"🏥 CLÍNICA: {clinic.name.upper()} (Schema: {clinic.schema_name})")
        print(f"{'─'*70}")
        
        # Obtener datos del admin para esta clínica
        admin_data = admins_data.get(clinic.schema_name)
        
        if not admin_data:
            print(f"⚠️  No hay datos de admin configurados para '{clinic.schema_name}'")
            print(f"   Saltando...")
            continue
        
        # Crear admin
        admin = create_clinic_admin(clinic, admin_data)
        if admin:
            created_admins.append({
                'clinic': clinic.name,
                'schema': clinic.schema_name,
                'email': admin.email,
                'password': admin_data['password']
            })
    
    return created_admins

def show_summary(admins):
    """Mostrar resumen de credenciales"""
    print("\n" + "="*70)
    print("📝 RESUMEN DE CREDENCIALES CREADAS")
    print("="*70)
    
    print("\n🌐 SUPERUSUARIO GLOBAL:")
    print("   📧 Email: admin@psicoadmin.xyz")
    print("   🔑 Password: admin123")
    print("   🌐 URL: https://psico-admin.onrender.com/admin/")
    print("   ℹ️  Acceso: Django Admin principal")
    
    print("\n🏥 ADMINISTRADORES DE CLÍNICAS:")
    for admin in admins:
        print(f"\n   {admin['clinic'].upper()} ({admin['schema']}):")
        print(f"   📧 Email: {admin['email']}")
        print(f"   🔑 Password: {admin['password']}")
        print(f"   🌐 Frontend: https://{admin['schema']}-app.psicoadmin.xyz/login")
        print(f"   🔧 Django Admin: https://{admin['schema']}.psicoadmin.xyz/admin/")

def main():
    print("\n🚀 INICIANDO CREACIÓN DE ADMINISTRADORES")
    print("📅 Fecha: 2025-10-21")
    
    # 1. Crear superusuario global
    superuser = create_global_superuser()
    
    # 2. Crear administradores de clínicas
    clinic_admins = create_all_clinic_admins()
    
    # 3. Mostrar resumen
    show_summary(clinic_admins)
    
    print("\n" + "="*70)
    print("✅ PROCESO COMPLETADO")
    print("="*70)
    
    print("\n⚠️  IMPORTANTE:")
    print("   - Todas las contraseñas son: admin123")
    print("   - Cambia estas contraseñas en producción real")
    print("   - Guarda estas credenciales en un lugar seguro")
    
    print("\n📋 PRÓXIMOS PASOS:")
    print("   1. Prueba login en el frontend:")
    print("      https://bienestar-app.psicoadmin.xyz/login")
    print("   2. Verifica acceso al Django Admin:")
    print("      https://psico-admin.onrender.com/admin/")
    print("   3. Prueba con las credenciales mostradas arriba")
    print()

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"\n❌ ERROR CRÍTICO: {e}")
        import traceback
        traceback.print_exc()
