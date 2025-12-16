"""
Comando para poblar la base de datos con historiales clínicos de ejemplo
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.clinical_history.models import ClinicalHistory
from apps.users.models import CustomUser
from apps.appointments.models import Appointment
from apps.tenants.models import Clinic
from django_tenants.utils import schema_context
import random
from datetime import datetime, timedelta

class Command(BaseCommand):
    help = 'Poblar la base de datos con historiales clínicos de ejemplo'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tenant',
            type=str,
            help='Schema del tenant específico (ej: mindcare, bienestar)',
            default=None
        )
        parser.add_argument(
            '--count',
            type=int,
            help='Número de historiales a crear por tenant',
            default=10
        )

    def handle(self, *args, **options):
        count = options['count']
        specific_tenant = options.get('tenant')
        
        self.stdout.write(self.style.SUCCESS('🏥 Iniciando poblado de historiales clínicos...'))
        
        # Obtener tenants
        if specific_tenant:
            tenants = Clinic.objects.filter(schema_name=specific_tenant)
            if not tenants.exists():
                self.stdout.write(self.style.ERROR(f'❌ Tenant "{specific_tenant}" no encontrado'))
                return
        else:
            tenants = Clinic.objects.exclude(schema_name='public')
        
        total_created = 0
        
        for tenant in tenants:
            self.stdout.write(f'📋 Poblando tenant: {tenant.name} ({tenant.schema_name})')
            
            with schema_context(tenant.schema_name):
                created_count = self._populate_tenant_histories(count)
                total_created += created_count
                self.stdout.write(f'   ✅ {created_count} historiales creados en {tenant.name}')
        
        self.stdout.write(
            self.style.SUCCESS(f'🎉 ¡Poblado completado! Total: {total_created} historiales clínicos creados')
        )

    def _populate_tenant_histories(self, count):
        """Poblar historiales para un tenant específico"""
        
        # Obtener pacientes que aún no tienen historial
        patients_without_history = CustomUser.objects.filter(
            user_type='patient'
        ).exclude(
            id__in=ClinicalHistory.objects.values_list('patient_id', flat=True)
        )
        
        # Obtener profesionales
        professionals = CustomUser.objects.filter(user_type='professional')
        
        if not patients_without_history.exists():
            return 0
        
        if not professionals.exists():
            return 0
        
        # Limitar la cantidad según los pacientes disponibles
        actual_count = min(count, patients_without_history.count())
        selected_patients = random.sample(list(patients_without_history), actual_count)
        
        created_count = 0
        
        for patient in selected_patients:
            # Seleccionar un profesional aleatorio que haya tenido citas con este paciente
            # Si no hay citas, usar cualquier profesional
            patient_professionals = professionals.filter(
                psychologist_appointments__patient=patient
            ).distinct()
            
            if patient_professionals.exists():
                professional = random.choice(patient_professionals)
            else:
                professional = random.choice(professionals)
            
            # Crear historial clínico con datos realistas
            history_data = self._generate_realistic_history_data()
            
            try:
                with transaction.atomic():
                    history = ClinicalHistory.objects.create(
                        patient=patient,
                        created_by=professional,
                        last_updated_by=professional,
                        **history_data
                    )
                    created_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'⚠️  Error creando historial para {patient.get_full_name()}: {e}')
                )
        
        return created_count

    def _generate_realistic_history_data(self):
        """Generar datos realistas para el historial clínico"""
        
        # Motivos de consulta comunes
        consultation_reasons = [
            "Síntomas de ansiedad y preocupación excesiva",
            "Estado de ánimo deprimido y pérdida de interés",
            "Dificultades para conciliar el sueño",
            "Problemas de autoestima y confianza",
            "Estrés laboral y burnout",
            "Problemas de pareja y comunicación",
            "Duelo por pérdida familiar",
            "Dificultades de adaptación a cambios",
            "Fobias específicas y ataques de pánico",
            "Problemas de concentración y memoria",
            "Conflictos familiares y generacionales",
            "Trastornos alimentarios",
            "Adicciones y dependencias",
            "Trauma por eventos pasados",
            "Problemas de control de impulsos"
        ]
        
        # Historias de enfermedad
        illness_histories = [
            "Paciente refiere sintomatología de aproximadamente 6 meses de evolución, caracterizada por episodios intermitentes de ansiedad.",
            "Cuadro clínico de inicio insidioso hace 3 meses, con predominio de síntomas del estado de ánimo.",
            "Historia de síntomas recurrentes desde la adolescencia, con exacerbaciones en períodos de estrés.",
            "Sintomatología aguda de 2 semanas de duración, posterior a evento traumático específico.",
            "Evolución crónica con períodos de mejoría y recaída, requiere seguimiento continuado.",
            "Primer episodio de estas características, sin antecedentes psiquiátricos previos.",
            "Cuadro reactivo a situación estresante laboral, con deterioro funcional progresivo.",
            "Síntomas fluctuantes relacionados con ciclos estacionales y cambios ambientales."
        ]
        
        # Antecedentes patológicos
        pathological_histories = [
            "Sin antecedentes psiquiátricos relevantes",
            "Episodio depresivo tratado hace 2 años con buena respuesta",
            "Historia familiar de trastornos del estado de ánimo",
            "Antecedente de trastorno de ansiedad en la adolescencia",
            "Sin hospitalizaciones psiquiátricas previas",
            "Tratamiento psicológico previo con resultados parciales",
            "Historia de consumo ocasional de alcohol",
            "Antecedente de trauma en la infancia"
        ]
        
        # Antecedentes familiares
        family_histories = [
            "Madre con historia de depresión, padre sin antecedentes relevantes",
            "Antecedentes familiares negativos para trastornos mentales",
            "Hermano con diagnóstico de trastorno bipolar",
            "Familia con tendencia a la ansiedad y preocupación excesiva",
            "Padre con problemas de alcohol, madre estable emocionalmente",
            "Abuelos maternos con historia de 'nervios' según relato familiar",
            "Sin información completa sobre antecedentes familiares",
            "Familia numerosa, varios miembros con dificultades emocionales"
        ]
        
        # Códigos diagnósticos comunes CIE-10
        diagnoses_options = [
            [{"codigo": "F32.1", "descripcion": "Episodio depresivo moderado", "fecha": "2025-10-05"}],
            [{"codigo": "F41.1", "descripcion": "Trastorno de ansiedad generalizada", "fecha": "2025-10-05"}],
            [{"codigo": "F43.1", "descripcion": "Trastorno de estrés postraumático", "fecha": "2025-10-05"}],
            [{"codigo": "F40.1", "descripcion": "Fobia social", "fecha": "2025-10-05"}],
            [{"codigo": "F42.2", "descripcion": "Trastorno obsesivo-compulsivo mixto", "fecha": "2025-10-05"}],
            [{"codigo": "F48.0", "descripcion": "Neurastenia", "fecha": "2025-10-05"}],
            [
                {"codigo": "F41.1", "descripcion": "Trastorno de ansiedad generalizada", "fecha": "2025-10-05"},
                {"codigo": "F32.0", "descripcion": "Episodio depresivo leve", "fecha": "2025-10-05"}
            ]
        ]
        
        # Planes terapéuticos
        therapeutic_plans = [
            {
                "modalidad": "Terapia cognitivo-conductual",
                "frecuencia": "Semanal",
                "duracion_estimada": "3-6 meses",
                "objetivos": [
                    "Reducir síntomas de ansiedad",
                    "Mejorar estrategias de afrontamiento",
                    "Incrementar autoestima"
                ],
                "tecnicas": ["Reestructuración cognitiva", "Técnicas de relajación", "Exposición gradual"]
            },
            {
                "modalidad": "Terapia humanista",
                "frecuencia": "Quincenal",
                "duracion_estimada": "6-12 meses",
                "objetivos": [
                    "Mejorar autoconocimiento",
                    "Fortalecer recursos personales",
                    "Desarrollar autonomía"
                ],
                "tecnicas": ["Escucha activa", "Reflejo empático", "Clarificación emocional"]
            },
            {
                "modalidad": "Terapia sistémica",
                "frecuencia": "Semanal",
                "duracion_estimada": "4-8 meses",
                "objetivos": [
                    "Mejorar comunicación familiar",
                    "Resolver conflictos interpersonales",
                    "Fortalecer vínculos"
                ],
                "tecnicas": ["Genograma", "Técnicas circulares", "Prescripciones paradójicas"]
            }
        ]
        
        # Evaluaciones de riesgo
        risk_assessments = [
            {"autolesion": "Bajo", "heteroagresion": "Nulo", "recaida": "Moderado"},
            {"autolesion": "Nulo", "heteroagresion": "Bajo", "recaida": "Bajo"},
            {"autolesion": "Moderado", "heteroagresion": "Nulo", "recaida": "Alto"},
            {"autolesion": "Bajo", "heteroagresion": "Nulo", "recaida": "Bajo"},
            {"autolesion": "Nulo", "heteroagresion": "Nulo", "recaida": "Moderado"}
        ]
        
        # Exámenes mentales
        mental_examinations = [
            {
                "aspecto": "Cuidado, vestimenta apropiada",
                "conciencia": "Lúcido y orientado",
                "atencion": "Conservada",
                "memoria": "Sin alteraciones evidentes",
                "pensamiento": "Organizado, sin ideas delirantes",
                "lenguaje": "Fluido y coherente",
                "afecto": "Ansioso pero colaborador",
                "juicio": "Conservado",
                "insight": "Parcial"
            },
            {
                "aspecto": "Descuidado, poca higiene personal",
                "conciencia": "Vigil, orientado",
                "atencion": "Dificultades de concentración",
                "memoria": "Quejas subjetivas de olvidos",
                "pensamiento": "Enlentecido, rumiaciones",
                "lenguaje": "Pausado, tono bajo",
                "afecto": "Deprimido, lábil",
                "juicio": "Conservado",
                "insight": "Bueno"
            }
        ]
        
        # Antecedentes no patológicos
        non_pathological_histories = [
            {
                "alimentacion": "Dieta balanceada, 3 comidas principales",
                "sueno": "7-8 horas nocturnas, sin alteraciones",
                "ejercicio": "Caminatas ocasionales",
                "sustancias": "Alcohol social ocasional",
                "trabajo": "Empleado de oficina, horario regular",
                "relaciones": "Pareja estable, círculo social reducido"
            },
            {
                "alimentacion": "Irregular, tendencia a saltarse comidas",
                "sueno": "Insomnio de conciliación, 5-6 horas",
                "ejercicio": "Sedentario",
                "sustancias": "No consumo",
                "trabajo": "Desempleado actualmente",
                "relaciones": "Soltero, vive con familia"
            },
            {
                "alimentacion": "Tres comidas al día, sin restricciones",
                "sueno": "8 horas, despertares nocturnos frecuentes",
                "ejercicio": "Gimnasio 3 veces por semana",
                "sustancias": "Café excesivo, no alcohol",
                "trabajo": "Profesional independiente",
                "relaciones": "Casado, 2 hijos"
            }
        ]
        
        # Temas sensibles
        sensitive_topics_options = [
            "Abuso emocional en relación de pareja anterior",
            "Dificultades económicas familiares",
            "Problemas de fertilidad y maternidad",
            "Conflictos laborales con superiores",
            "Duelo no resuelto por muerte de padre",
            "Secreto familiar sobre adopción",
            "Problemas de identidad sexual",
            "Bullying escolar en la adolescencia",
            "Enfermedad crónica no revelada a la familia",
            "Adicción oculta a medicamentos"
        ]
        
        return {
            'consultation_reason': random.choice(consultation_reasons),
            'history_of_illness': random.choice(illness_histories),
            'personal_pathological_history': random.choice(pathological_histories),
            'family_history': random.choice(family_histories),
            'personal_non_pathological_history': random.choice(non_pathological_histories),
            'mental_examination': random.choice(mental_examinations),
            'complementary_tests': "Pendiente realización de escalas psicométricas específicas",
            'diagnoses': random.choice(diagnoses_options),
            'therapeutic_plan': random.choice(therapeutic_plans),
            'risk_assessment': random.choice(risk_assessments),
            'sensitive_topics': random.choice(sensitive_topics_options)
        }