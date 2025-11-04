"""
Comando para mostrar información del sistema de backups
"""

from django.core.management.base import BaseCommand
from apps.tenants.models import Clinic
from django.conf import settings

class Command(BaseCommand):
    help = 'Mostrar información del sistema de copias de seguridad'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('💾 Sistema de Copias de Seguridad - Fase 1'))
        self.stdout.write('=' * 60)
        
        # Información del sistema
        db_settings = settings.DATABASES['default']
        self.stdout.write(f'\n📊 Configuración de Base de Datos:')
        self.stdout.write(f'   - Motor: {db_settings["ENGINE"]}')
        self.stdout.write(f'   - Host: {db_settings["HOST"]}')
        self.stdout.write(f'   - Puerto: {db_settings["PORT"]}')
        self.stdout.write(f'   - Base de datos: {db_settings["NAME"]}')
        
        # Tenants disponibles
        tenants = Clinic.objects.exclude(schema_name='public')
        self.stdout.write(f'\n🏥 Tenants disponibles para backup:')
        for tenant in tenants:
            self.stdout.write(f'   - {tenant.name} (schema: {tenant.schema_name})')
        
        # Endpoints disponibles
        self.stdout.write(f'\n🌐 Endpoints de la API:')
        self.stdout.write(f'   POST /api/backups/create/  -> Crear y descargar backup')
        self.stdout.write(f'   POST /api/backups/restore/ -> Restaurar desde archivo')
        
        # Métodos de backup
        self.stdout.write(f'\n🔧 Métodos de backup soportados:')
        self.stdout.write(f'   1. PostgreSQL nativo (pg_dump/psql) - Archivos .sql')
        self.stdout.write(f'   2. Restauración robusta: DROP CASCADE + CREATE + psql')
        self.stdout.write(f'   3. Validación de errores: check=True para detección confiable')
        
        # Formatos soportados
        self.stdout.write(f'\n📁 Formatos de archivo soportados:')
        self.stdout.write(f'   - .sql  -> Backup SQL de texto plano (recomendado)')
        self.stdout.write(f'   - .json -> Backup Django JSON (alternativo)')
        
        # Características mejoradas
        self.stdout.write(f'\n🛡️ Características de seguridad:')
        self.stdout.write(f'   - ✅ Protección contra restauración del esquema público')
        self.stdout.write(f'   - ✅ DROP CASCADE para limpiar esquemas bloqueados')
        self.stdout.write(f'   - ✅ Recreación completa del esquema antes de restaurar')
        self.stdout.write(f'   - ✅ Manejo de conexiones activas durante restauración')
        
        # Permisos
        self.stdout.write(f'\n🔐 Permisos requeridos:')
        self.stdout.write(f'   - Usuario autenticado')
        self.stdout.write(f'   - Rol de administrador de clínica (IsClinicAdmin)')
        
        # Ejemplos de uso
        self.stdout.write(f'\n📖 Ejemplos de uso:')
        if tenants.exists():
            tenant = tenants.first()
            self.stdout.write(f'   # Crear backup')
            self.stdout.write(f'   curl -X POST \\')
            self.stdout.write(f'        -H "Authorization: Token <your-token>" \\')
            self.stdout.write(f'        http://{tenant.schema_name}.localhost:8000/api/backups/create/')
            self.stdout.write(f'')
            self.stdout.write(f'   # Restaurar backup')
            self.stdout.write(f'   curl -X POST \\')
            self.stdout.write(f'        -H "Authorization: Token <your-token>" \\')
            self.stdout.write(f'        -F "backup_file=@backup-{tenant.schema_name}-2025-10-06.sql" \\')
            self.stdout.write(f'        http://{tenant.schema_name}.localhost:8000/api/backups/restore/')
        
        # Características implementadas
        self.stdout.write(f'\n✅ Características implementadas:')
        self.stdout.write(f'   - ✅ Backup por tenant individual')
        self.stdout.write(f'   - ✅ Descarga directa desde navegador')
        self.stdout.write(f'   - ✅ Restauración robusta con DROP CASCADE')
        self.stdout.write(f'   - ✅ Compatibilidad con/sin herramientas PostgreSQL')
        self.stdout.write(f'   - ✅ Manejo de errores robusto')
        self.stdout.write(f'   - ✅ Integración con sistema multi-tenant')
        self.stdout.write(f'   - ✅ Permisos de seguridad aplicados')
        self.stdout.write(f'   - ✅ Solución para conexiones activas de base de datos')
        
        # Estado del sistema
        self.stdout.write(f'\n🎯 Estado actual:')
        self.stdout.write(f'   - ✅ Fase 1: Backend API completado')
        self.stdout.write(f'   - ⏳ Fase 2: Interfaz de usuario (pendiente)')
        self.stdout.write(f'   - ⏳ Fase 3: Automatización y programación (pendiente)')
        
        self.stdout.write(self.style.SUCCESS(f'\n🚀 ¡Sistema de backups listo para usar!'))