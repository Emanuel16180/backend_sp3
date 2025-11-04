#!/usr/bin/env python
"""
Script para marcar profesionales como verificados y con perfil completo
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from apps.professionals.models import ProfessionalProfile

print("=" * 60)
print("✅ VERIFICANDO Y COMPLETANDO PERFILES")
print("=" * 60)

tenants = ['bienestar', 'mindcare']

for tenant_name in tenants:
    print(f"\n🏥 Procesando: {tenant_name}")
    
    with schema_context(tenant_name):
        profiles = ProfessionalProfile.objects.all()
        
        for profile in profiles:
            changed = False
            
            if not profile.is_verified:
                profile.is_verified = True
                changed = True
            
            if not profile.profile_completed:
                profile.profile_completed = True
                changed = True
            
            if not profile.is_active:
                profile.is_active = True
                changed = True
            
            if changed:
                profile.save()
                print(f"   ✅ {profile.user.get_full_name()} actualizado")
        
        # Mostrar resumen
        total = profiles.count()
        verified = profiles.filter(is_verified=True).count()
        completed = profiles.filter(profile_completed=True).count()
        active = profiles.filter(is_active=True).count()
        
        print(f"   📊 Total: {total} | Verificados: {verified} | Completos: {completed} | Activos: {active}")

print("\n" + "=" * 60)
print("🎉 ¡Todos los perfiles actualizados!")
print("=" * 60)
