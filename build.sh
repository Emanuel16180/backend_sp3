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
