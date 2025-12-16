#!/usr/bin/env python
"""
Script rápido para crear el tenant público y dominios para desarrollo local
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.tenants.models import Clinic, Domain


def create_public_tenant():
    clinic, created = Clinic.objects.get_or_create(
        schema_name='public',
        defaults={'name': 'Public Clinic (local)'}
    )
    if created:
        print(f"✅ Clínica pública creada: {clinic.name} (schema: {clinic.schema_name})")
    else:
        print(f"ℹ️  Clínica pública existente: {clinic.name} (schema: {clinic.schema_name})")

    # Dominios útiles para desarrollo local
    for dom in ['127.0.0.1', 'localhost']:
        domain_obj, dcreated = Domain.objects.get_or_create(
            domain=dom,
            defaults={
                'tenant': clinic,
                'is_primary': True if dom == '127.0.0.1' else False
            }
        )
        if dcreated:
            print(f"   🌐 Dominio creado: {domain_obj.domain}")
        else:
            print(f"   🌐 Dominio existente: {domain_obj.domain}")

    print('\n✅ Public tenant listo. Intenta acceder a http://127.0.0.1:8000/admin/')


if __name__ == '__main__':
    try:
        create_public_tenant()
    except Exception as e:
        print('Error creando tenant público:', e)
        import traceback
        traceback.print_exc()
