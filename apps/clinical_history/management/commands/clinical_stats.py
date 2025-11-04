"""
Comando para mostrar estadísticas de los historiales clínicos
"""

from django.core.management.base import BaseCommand
from apps.clinical_history.models import ClinicalHistory
from apps.users.models import CustomUser
from apps.tenants.models import Clinic
from django_tenants.utils import schema_context
from django.db.models import Count

class Command(BaseCommand):
    help = 'Mostrar estadísticas de los historiales clínicos'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            help='Schema del tenant específico (ej: mindcare, bienestar)',
            default=None
        )
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Mostrar información detallada de cada historial',
        )

    def handle(self, *args, **options):
        specific_tenant = options.get('tenant')
        detailed = options.get('detailed', False)
        
        self.stdout.write(self.style.SUCCESS('📊 Estadísticas de Historiales Clínicos'))
        self.stdout.write('=' * 60)
        
        # Obtener tenants
        if specific_tenant:
            tenants = Clinic.objects.filter(schema_name=specific_tenant)
            if not tenants.exists():
                self.stdout.write(self.style.ERROR(f'❌ Tenant "{specific_tenant}" no encontrado'))
                return
        else:
            tenants = Clinic.objects.exclude(schema_name='public')
        
        total_histories = 0
        total_patients_with_history = 0
        total_patients = 0
        
        for tenant in tenants:
            self.stdout.write(f'\n🏥 {tenant.name} ({tenant.schema_name})')
            self.stdout.write('-' * 50)
            
            with schema_context(tenant.schema_name):
                # Estadísticas básicas
                histories_count = ClinicalHistory.objects.count()
                patients_count = CustomUser.objects.filter(user_type='patient').count()
                patients_with_history = ClinicalHistory.objects.values('patient').distinct().count()
                professionals_count = CustomUser.objects.filter(user_type='professional').count()
                
                total_histories += histories_count
                total_patients_with_history += patients_with_history
                total_patients += patients_count
                
                self.stdout.write(f'📋 Historiales clínicos: {histories_count}')
                self.stdout.write(f'👥 Pacientes totales: {patients_count}')
                self.stdout.write(f'📝 Pacientes con historial: {patients_with_history}')
                self.stdout.write(f'👨‍⚕️ Profesionales: {professionals_count}')
                
                if patients_count > 0:
                    coverage = (patients_with_history / patients_count) * 100
                    self.stdout.write(f'📊 Cobertura de historiales: {coverage:.1f}%')
                
                # Mostrar detalles si se solicita
                if detailed and histories_count > 0:
                    self.stdout.write('\n📋 Historiales detallados:')
                    histories = ClinicalHistory.objects.select_related(
                        'patient', 'created_by', 'last_updated_by'
                    ).all()
                    
                    for i, history in enumerate(histories, 1):
                        self.stdout.write(f'\n  {i}. 👤 {history.patient.get_full_name()}')
                        
                        created_by = "N/A"
                        if history.created_by:
                            created_by = history.created_by.get_full_name()
                        
                        updated_by = "N/A"
                        if history.last_updated_by:
                            updated_by = history.last_updated_by.get_full_name()
                        
                        self.stdout.write(f'     📅 Creado: {history.created_at.strftime("%d/%m/%Y")} por {created_by}')
                        self.stdout.write(f'     🔄 Actualizado: {history.updated_at.strftime("%d/%m/%Y")} por {updated_by}')
                        self.stdout.write(f'     📝 Motivo: {history.consultation_reason[:50]}...')
                        
                        # Mostrar diagnósticos si existen
                        if history.diagnoses:
                            diagnoses_list = [d.get('descripcion', 'N/A') for d in history.diagnoses]
                            self.stdout.write(f'     🔍 Diagnósticos: {", ".join(diagnoses_list)}')
                        
                        # Mostrar evaluación de riesgos
                        if history.risk_assessment:
                            risks = history.risk_assessment
                            self.stdout.write(f'     ⚠️ Riesgos: Autolesión={risks.get("autolesion", "N/A")}, Recaída={risks.get("recaida", "N/A")}')
        
        # Resumen final
        self.stdout.write(f'\n🎯 RESUMEN GENERAL')
        self.stdout.write('=' * 30)
        self.stdout.write(f'📊 Total historiales: {total_histories}')
        self.stdout.write(f'👥 Total pacientes: {total_patients}')
        self.stdout.write(f'📝 Pacientes con historial: {total_patients_with_history}')
        self.stdout.write(f'🏥 Tenants activos: {tenants.count()}')
        
        if total_patients > 0:
            global_coverage = (total_patients_with_history / total_patients) * 100
            self.stdout.write(f'📊 Cobertura global: {global_coverage:.1f}%')
        
        self.stdout.write(f'\n🌐 API Endpoints disponibles:')
        self.stdout.write(f'   GET /api/clinical-history/patient/<patient_id>/')
        self.stdout.write(f'   PUT /api/clinical-history/patient/<patient_id>/')
        self.stdout.write(f'   PATCH /api/clinical-history/patient/<patient_id>/')
        
        # Mostrar ejemplo de uso
        if total_histories > 0:
            self.stdout.write(f'\n📖 Ejemplo de uso:')
            with schema_context(tenants.first().schema_name):
                sample_patient = CustomUser.objects.filter(user_type='patient').first()
                if sample_patient:
                    tenant_schema = tenants.first().schema_name
                    self.stdout.write(f'   curl -H "Authorization: Token <your-token>" \\')
                    self.stdout.write(f'        http://{tenant_schema}.localhost:8000/api/clinical-history/patient/{sample_patient.id}/')
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Sistema de historiales clínicos operativo!'))