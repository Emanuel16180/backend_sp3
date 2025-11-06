#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🔧 Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🗄️ Aplicando migraciones al esquema público..."
python manage.py migrate_schemas --shared

echo "📁 Recolectando archivos estáticos..."
python manage.py collectstatic --no-input

echo "🏥 Creando clínicas de demostración..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.tenants.models import Clinic, Domain
from django_tenants.utils import get_public_schema_name

# Obtener el tenant público
public_tenant = Clinic.objects.get(schema_name=get_public_schema_name())

# Agregar dominio para api.psicoadmin.xyz al tenant público
Domain.objects.get_or_create(
    domain='api.psicoadmin.xyz',
    defaults={
        'tenant': public_tenant,
        'is_primary': False
    }
)
print('✅ Dominio api.psicoadmin.xyz agregado al tenant público')

# Crear Bienestar si no existe
bienestar, created = Clinic.objects.get_or_create(
    schema_name='bienestar',
    defaults={'name': 'Clínica Bienestar'}
)
if created:
    print('✅ Clínica Bienestar creada')
else:
    print('⚠️ Clínica Bienestar ya existe')

# Limpiar dominios duplicados y crear el correcto
Domain.objects.filter(tenant=bienestar).delete()
Domain.objects.create(
    domain='bienestar.psicoadmin.xyz',
    tenant=bienestar,
    is_primary=True
)
print('✅ Dominio de Bienestar configurado')

# Crear Mindcare si no existe
mindcare, created = Clinic.objects.get_or_create(
    schema_name='mindcare',
    defaults={'name': 'Clínica Mindcare'}
)
if created:
    print('✅ Clínica Mindcare creada')
else:
    print('⚠️ Clínica Mindcare ya existe')

# Limpiar dominios duplicados y crear el correcto
Domain.objects.filter(tenant=mindcare).delete()
Domain.objects.create(
    domain='mindcare.psicoadmin.xyz',
    tenant=mindcare,
    is_primary=True
)
print('✅ Dominio de Mindcare configurado')

print('🎉 Clínicas y dominios configurados correctamente')
"

echo "📊 Aplicando migraciones a los tenants..."
python manage.py migrate_schemas || echo "⚠️ Error en migraciones de tenants"

echo "✅ Build completado!"
