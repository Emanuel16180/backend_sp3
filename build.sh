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
        admin = CustomUser(
            email='admin@bienestar.com',
            username='admin_bienestar',
            first_name='Admin',
            last_name='Bienestar',
            user_type='admin',
            is_staff=True,
            is_superuser=True
        )
        admin.set_password('admin123')
        admin.save()
        print('✅ Admin de Bienestar creado')
    
    # Profesional
    if not CustomUser.objects.filter(email='dra.martinez@bienestar.com').exists():
        prof = CustomUser(
            email='dra.martinez@bienestar.com',
            username='dra_martinez_bienestar',
            first_name='Laura',
            last_name='Martínez',
            user_type='professional'
        )
        prof.set_password('demo123')
        prof.save()
        print('✅ Profesional de Bienestar creado')
    
    # Paciente
    if not CustomUser.objects.filter(email='juan.perez@example.com').exists():
        patient = CustomUser(
            email='juan.perez@example.com',
            username='juan_perez_bienestar',
            first_name='Juan',
            last_name='Pérez',
            user_type='patient'
        )
        patient.set_password('demo123')
        patient.save()
        print('✅ Paciente de Bienestar creado')

# Crear usuarios en Mindcare
with schema_context('mindcare'):
    # Admin
    if not CustomUser.objects.filter(email='admin@mindcare.com').exists():
        admin = CustomUser(
            email='admin@mindcare.com',
            username='admin_mindcare',
            first_name='Admin',
            last_name='Mindcare',
            user_type='admin',
            is_staff=True,
            is_superuser=True
        )
        admin.set_password('admin123')
        admin.save()
        print('✅ Admin de Mindcare creado')
    
    # Profesional
    if not CustomUser.objects.filter(email='dr.garcia@mindcare.com').exists():
        prof = CustomUser(
            email='dr.garcia@mindcare.com',
            username='dr_garcia_mindcare',
            first_name='Carlos',
            last_name='García',
            user_type='professional'
        )
        prof.set_password('demo123')
        prof.save()
        print('✅ Profesional de Mindcare creado')
    
    # Paciente
    if not CustomUser.objects.filter(email='maria.lopez@example.com').exists():
        patient = CustomUser(
            email='maria.lopez@example.com',
            username='maria_lopez_mindcare',
            first_name='María',
            last_name='López',
            user_type='patient'
        )
        patient.set_password('demo123')
        patient.save()
        print('✅ Paciente de Mindcare creado')

print('🎉 Usuarios de demostración creados')
"

echo "✅ Build completado!"
