#!/usr/bin/env python
"""
🗑️ SCRIPT DE LIMPIEZA Y RESET COMPLETO
=========================================
Este script elimina TODOS los datos y reinicia el sistema desde cero.

⚠️ ADVERTENCIA: Esta operación es IRREVERSIBLE
⚠️ Se perderán TODOS los datos de TODAS las clínicas

USO:
    python reset_database.py

REQUISITOS:
    - Confirmar la operación manualmente
    - Base de datos PostgreSQL accesible
"""

import os
import sys
import django
from pathlib import Path

# Configurar Django
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.core.management import call_command
from apps.tenants.models import Clinic, Domain
from django.db import connection


def print_header(message):
    """Imprimir encabezado decorado"""
    print("\n" + "=" * 60)
    print(f"  {message}")
    print("=" * 60)


def drop_all_schemas():
    """Eliminar todos los schemas excepto los del sistema"""
    print("\n🗑️  Eliminando schemas...")
    
    # Obtener lista de schemas a eliminar
    clinics = Clinic.objects.all()
    
    for clinic in clinics:
        schema_name = clinic.schema_name
        
        # No eliminar schemas del sistema
        if schema_name in ['public', 'information_schema', 'pg_catalog']:
            continue
        
        try:
            with connection.cursor() as cursor:
                print(f"   🗑️  Eliminando schema: {schema_name}")
                cursor.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')
                print(f"   ✅ Schema {schema_name} eliminado")
        except Exception as e:
            print(f"   ⚠️  Error eliminando {schema_name}: {e}")
    
    # Limpiar tabla de clínicas en public
    print("\n   🗑️  Limpiando tabla de clínicas...")
    Clinic.objects.all().delete()
    Domain.objects.all().delete()
    print("   ✅ Tablas de tenants limpiadas")


def reset_migrations():
    """Limpiar archivos de migración (opcional)"""
    print("\n📦 Limpiando historial de migraciones...")
    
    apps_dir = BASE_DIR / 'apps'
    
    for app_path in apps_dir.iterdir():
        if not app_path.is_dir():
            continue
        
        migrations_dir = app_path / 'migrations'
        if not migrations_dir.exists():
            continue
        
        # Eliminar archivos de migración excepto __init__.py
        for migration_file in migrations_dir.glob('*.py'):
            if migration_file.name == '__init__.py':
                continue
            
            try:
                migration_file.unlink()
                print(f"   🗑️  Eliminado: {migration_file.name}")
            except Exception as e:
                print(f"   ⚠️  Error eliminando {migration_file.name}: {e}")
        
        # Limpiar cache
        pycache_dir = migrations_dir / '__pycache__'
        if pycache_dir.exists():
            for cache_file in pycache_dir.glob('*'):
                try:
                    cache_file.unlink()
                except:
                    pass


def recreate_migrations():
    """Recrear migraciones desde cero"""
    print("\n📦 Recreando migraciones...")
    
    try:
        call_command('makemigrations', verbosity=1)
        print("   ✅ Migraciones recreadas")
    except Exception as e:
        print(f"   ⚠️  Error recreando migraciones: {e}")


def confirm_operation():
    """Solicitar confirmación del usuario"""
    print_header("⚠️  ADVERTENCIA - OPERACIÓN DESTRUCTIVA")
    
    print("\n❗ Esta operación eliminará:")
    print("  ❌ TODOS los schemas de las clínicas")
    print("  ❌ TODOS los usuarios")
    print("  ❌ TODOS los pacientes")
    print("  ❌ TODOS los profesionales")
    print("  ❌ TODAS las citas")
    print("  ❌ TODOS los datos del sistema")
    
    print("\n🔴 Esta acción es IRREVERSIBLE")
    print("🔴 Se recomienda hacer un respaldo antes de continuar")
    
    print("\n" + "=" * 60)
    
    # Primera confirmación
    response1 = input("\n¿Estás seguro de querer continuar? (escribe 'SI' en mayúsculas): ").strip()
    if response1 != 'SI':
        return False
    
    # Segunda confirmación
    response2 = input("\n¿REALMENTE deseas eliminar TODOS los datos? (escribe 'ELIMINAR'): ").strip()
    if response2 != 'ELIMINAR':
        return False
    
    return True


def main():
    """Función principal"""
    print_header("🗑️ RESET COMPLETO DE BASE DE DATOS")
    
    # Solicitar confirmación
    if not confirm_operation():
        print("\n✅ Operación cancelada de forma segura")
        print("   No se eliminó ningún dato")
        sys.exit(0)
    
    print_header("🔄 INICIANDO PROCESO DE RESET")
    
    # Paso 1: Eliminar schemas
    drop_all_schemas()
    
    # Paso 2: Preguntar si resetear migraciones
    print("\n" + "=" * 60)
    reset_mig = input("¿Deseas resetear las migraciones también? (s/n): ").strip().lower()
    
    if reset_mig == 's':
        reset_migrations()
        recreate_migrations()
    
    # Resumen
    print_header("✅ RESET COMPLETADO")
    
    print("\n📊 Estado actual:")
    print("  ✅ Todos los schemas eliminados")
    print("  ✅ Tablas de tenants limpiadas")
    
    if reset_mig == 's':
        print("  ✅ Migraciones reseteadas")
    
    print("\n🚀 PRÓXIMOS PASOS:")
    print("  1. Ejecutar: python setup_complete.py")
    print("     (para recrear todo el sistema desde cero)")
    print("\n  O bien:")
    print("  1. python manage.py migrate")
    print("  2. python create_public_tenant.py")
    print("  3. python create_tenants.py")
    print("  4. python populate_demo_data.py")
    
    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operación cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
