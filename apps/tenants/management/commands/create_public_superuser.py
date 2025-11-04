# apps/tenants/management/commands/create_public_superuser.py

from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context
from apps.tenants.models import PublicUser
import getpass

class Command(BaseCommand):
    help = 'Crea un superusuario en el esquema público para gestionar clínicas.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            help='Email del superusuario (opcional, se pedirá interactivamente si no se proporciona)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING(
            '🏢 Creando superusuario GLOBAL para gestión de clínicas...'
        ))
        self.stdout.write(self.style.WARNING(
            'Este usuario podrá acceder al admin público en http://localhost:8000/admin/'
        ))
        
        # Obtener email
        email = options.get('email')
        if not email:
            email = input('📧 Email del superusuario global: ')
        
        # Obtener contraseña de forma segura
        password = getpass.getpass('🔐 Password: ')
        password_confirm = getpass.getpass('🔐 Confirmar password: ')
        
        if password != password_confirm:
            self.stdout.write(self.style.ERROR('❌ Las contraseñas no coinciden.'))
            return
        
        # Crear superusuario en el esquema público
        try:
            with schema_context('public'):
                if PublicUser.objects.filter(email=email).exists():
                    self.stdout.write(self.style.ERROR(
                        f'❌ Un usuario con el email "{email}" ya existe en el esquema público.'
                    ))
                    return

                user = PublicUser.objects.create_superuser(
                    email=email,
                    password=password,
                    first_name='Admin',
                    last_name='Global'
                )
                
                self.stdout.write(self.style.SUCCESS(
                    f'✅ Superusuario global "{user.email}" creado exitosamente.'
                ))
                self.stdout.write(self.style.SUCCESS(
                    '🔗 Ahora puedes acceder a: http://localhost:8000/admin/'
                ))
                self.stdout.write(self.style.WARNING(
                    '📋 Este admin solo gestiona clínicas, no datos de pacientes/psicólogos.'
                ))
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(
                f'❌ Error al crear superusuario: {e}'
            ))