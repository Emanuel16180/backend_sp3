#!/usr/bin/env python
"""
Script para crear las clínicas (tenants) y sus dominios
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.tenants.models import Clinic, Domain

def create_clinics():
    print("🏥 Creando clínicas...")
    
    # Clínica 1: Bienestar
    bienestar, created = Clinic.objects.get_or_create(
        schema_name='bienestar',
        defaults={'name': 'Clínica Bienestar'}
    )
    if created:
        print(f"✅ Clínica creada: {bienestar.name} (schema: {bienestar.schema_name})")
    else:
        print(f"ℹ️  Clínica existente: {bienestar.name} (schema: {bienestar.schema_name})")
    
    # Dominio para Bienestar
    domain_bienestar, created = Domain.objects.get_or_create(
        domain='bienestar.localhost',
        defaults={
            'tenant': bienestar,
            'is_primary': True
        }
    )
    if created:
        print(f"   🌐 Dominio creado: {domain_bienestar.domain}")
    else:
        print(f"   🌐 Dominio existente: {domain_bienestar.domain}")
    
    # Clínica 2: Mindcare
    mindcare, created = Clinic.objects.get_or_create(
        schema_name='mindcare',
        defaults={'name': 'Clínica Mindcare'}
    )
    if created:
        print(f"✅ Clínica creada: {mindcare.name} (schema: {mindcare.schema_name})")
    else:
        print(f"ℹ️  Clínica existente: {mindcare.name} (schema: {mindcare.schema_name})")
    
    # Dominio para Mindcare
    domain_mindcare, created = Domain.objects.get_or_create(
        domain='mindcare.localhost',
        defaults={
            'tenant': mindcare,
            'is_primary': True
        }
    )
    if created:
        print(f"   🌐 Dominio creado: {domain_mindcare.domain}")
    else:
        print(f"   🌐 Dominio existente: {domain_mindcare.domain}")
    
    print("\n📊 RESUMEN:")
    print(f"   Total clínicas: {Clinic.objects.count()}")
    print(f"   Total dominios: {Domain.objects.count()}")
    
    print("\n🔗 Acceso:")
    print(f"   - Bienestar: http://bienestar.localhost:8000/")
    print(f"   - Mindcare: http://mindcare.localhost:8000/")
    print(f"   - Admin Global: http://127.0.0.1:8000/admin/")

if __name__ == "__main__":
    try:
        create_clinics()
        print("\n✅ ¡Clínicas creadas exitosamente!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
