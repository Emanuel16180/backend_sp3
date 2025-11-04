# apps/tenants/management/commands/create_tenant.py

from django.core.management.base import BaseCommand
from apps.tenants.models import Clinic, Domain

class Command(BaseCommand):
    help = 'Crea un nuevo inquilino (clínica) y su dominio.'

    def add_arguments(self, parser):
        parser.add_argument('name', type=str, help='El nombre de la clínica.')
        parser.add_argument('schema_name', type=str, help='El nombre del esquema en la BD (ej. clinicabienestar).')
        parser.add_argument('domain', type=str, help='El dominio o subdominio para acceder (ej. bienestar.localhost).')

    def handle(self, *args, **options):
        name = options['name']
        schema_name = options['schema_name']
        domain_url = options['domain']

        # Crear la Clínica (esto creará el esquema automáticamente gracias a auto_create_schema=True)
        if Clinic.objects.filter(schema_name=schema_name).exists():
            self.stdout.write(self.style.ERROR(f'Ya existe una clínica con el schema_name "{schema_name}"'))
            return

        clinic = Clinic.objects.create(name=name, schema_name=schema_name)

        # Crear el Dominio asociado a la clínica
        domain = Domain()
        domain.domain = domain_url
        domain.tenant = clinic
        domain.is_primary = True
        domain.save()

        self.stdout.write(self.style.SUCCESS(
            f'¡Clínica "{name}" creada exitosamente con el dominio {domain_url}!'
        ))