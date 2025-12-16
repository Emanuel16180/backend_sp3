#!/usr/bin/env python
"""
Script para limpiar suscripciones antiguas de push notifications
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from apps.tenants.models import Clinic
from apps.notifications.models import PushSubscription

print("=" * 60)
print("LIMPIANDO SUSCRIPCIONES ANTIGUAS")
print("=" * 60)

# Trabajar en el tenant bienestar
tenant = Clinic.objects.get(schema_name='bienestar')

with schema_context(tenant.schema_name):
    # Eliminar todas las suscripciones existentes
    old_count = PushSubscription.objects.count()
    PushSubscription.objects.all().delete()
    
    print(f"\n✅ Eliminadas {old_count} suscripciones antiguas")
    print("   Ana debe suscribirse de nuevo con las nuevas claves VAPID")

print("\n" + "=" * 60)
