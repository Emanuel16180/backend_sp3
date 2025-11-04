#!/usr/bin/env python
"""
Script para listar TODOS los usuarios en bienestar
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from apps.users.models import CustomUser

print("=" * 60)
print("👥 TODOS LOS USUARIOS EN BIENESTAR")
print("=" * 60)

with schema_context('bienestar'):
    users = CustomUser.objects.all()
    
    if users.exists():
        for user in users:
            print(f"\n👤 {user.get_full_name()}")
            print(f"   Email: {user.email}")
            print(f"   Tipo: {user.user_type}")
            print(f"   Activo: {'✅' if user.is_active else '❌'}")
    else:
        print("\n❌ NO HAY USUARIOS EN BIENESTAR")
        print("\n💡 NECESITAS EJECUTAR: python populate_demo_data.py")

print("\n" + "=" * 60)
