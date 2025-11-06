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

echo "👤 Creando usuarios de demostración..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django_tenants.utils import schema_context
from apps.users.models import CustomUser

# Crear usuarios en Bienestar
with schema_context('bienestar'):
    # Admin
    if not CustomUser.objects.filter(email='admin@bienestar.com').exists():
        CustomUser.objects.create_superuser(
            email='admin@bienestar.com',
            password='admin123',
            first_name='Admin',
            last_name='Bienestar',
            user_type='admin'
        )
        print('✅ Admin de Bienestar creado')
    
    # Profesional
    if not CustomUser.objects.filter(email='dra.martinez@bienestar.com').exists():
        CustomUser.objects.create_user(
            email='dra.martinez@bienestar.com',
            password='demo123',
            first_name='Laura',
            last_name='Martínez',
            user_type='professional'
        )
        print('✅ Profesional de Bienestar creado')
    
    # Paciente
    if not CustomUser.objects.filter(email='juan.perez@example.com').exists():
        CustomUser.objects.create_user(
            email='juan.perez@example.com',
            password='demo123',
            first_name='Juan',
            last_name='Pérez',
            user_type='patient'
        )
        print('✅ Paciente de Bienestar creado')

# Crear usuarios en Mindcare
with schema_context('mindcare'):
    # Admin
    if not CustomUser.objects.filter(email='admin@mindcare.com').exists():
        CustomUser.objects.create_superuser(
            email='admin@mindcare.com',
            password='admin123',
            first_name='Admin',
            last_name='Mindcare',
            user_type='admin'
        )
        print('✅ Admin de Mindcare creado')
    
    # Profesional
    if not CustomUser.objects.filter(email='dr.garcia@mindcare.com').exists():
        CustomUser.objects.create_user(
            email='dr.garcia@mindcare.com',
            password='demo123',
            first_name='Carlos',
            last_name='García',
            user_type='professional'
        )
        print('✅ Profesional de Mindcare creado')
    
    # Paciente
    if not CustomUser.objects.filter(email='maria.lopez@example.com').exists():
        CustomUser.objects.create_user(
            email='maria.lopez@example.com',
            password='demo123',
            first_name='María',
            last_name='López',
            user_type='patient'
        )
        print('✅ Paciente de Mindcare creado')

print('🎉 Usuarios de demostración creados')
"

echo "✅ Build completado!"
