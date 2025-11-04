# apps/professionals/management/commands/create_sample_reviews.py

from django.core.management.base import BaseCommand
from apps.appointments.models import Appointment
from apps.professionals.models import Review
from django.contrib.auth import get_user_model
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Crea reseñas de ejemplo para probar el sistema'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Número de reseñas a crear (default: 10)'
        )

    def handle(self, *args, **options):
        count = options['count']
        
        # Obtener citas completadas sin reseña
        available_appointments = Appointment.objects.filter(
            status='completed'
        ).exclude(
            id__in=Review.objects.values_list('appointment_id', flat=True)
        )
        
        if not available_appointments.exists():
            self.stdout.write(
                self.style.WARNING('No hay citas completadas disponibles para reseñar')
            )
            return
        
        # Comentarios de ejemplo en español
        comments = [
            "Excelente profesional, muy empática y comprensiva. Me ayudó mucho en mi proceso.",
            "Muy buena atención, se nota su experiencia. Recomendado al 100%.",
            "Profesional muy preparada, me sentí cómodo durante toda la sesión.",
            "Muy buena terapeuta, técnicas efectivas y ambiente acogedor.",
            "Excelente trabajo, me ha ayudado a ver las cosas desde otra perspectiva.",
            "Muy profesional y puntual. Las sesiones son muy productivas.",
            "Gran capacidad de escucha y análisis. Muy recomendable.",
            "Me siento muy cómoda con su estilo terapéutico. Excelente profesional.",
            "Muy buena experiencia, profesional comprometida con sus pacientes.",
            "Técnicas muy efectivas y ambiente muy relajante. Muy satisfecho.",
            "Profesional muy capacitada, me ha ayudado mucho en mi crecimiento personal.",
            "Excelente atención y seguimiento. Muy recomendable.",
            "Muy buena comunicación y técnicas adaptadas a mis necesidades.",
            "Profesional excepcional, me ha ayudado a superar muchos obstáculos.",
            "Muy satisfecho con el tratamiento, profesional muy dedicada."
        ]
        
        created_count = 0
        max_to_create = min(count, available_appointments.count())
        
        # Crear reseñas aleatorias
        selected_appointments = random.sample(list(available_appointments), max_to_create)
        
        for appointment in selected_appointments:
            # Generar rating (más probabilidad de ratings altos)
            rating = random.choices([3, 4, 5], weights=[1, 3, 6])[0]
            
            # Seleccionar comentario aleatorio
            comment = random.choice(comments)
            
            try:
                review = Review.objects.create(
                    professional=appointment.psychologist.professional_profile,
                    patient=appointment.patient,
                    appointment=appointment,
                    rating=rating,
                    comment=comment
                )
                
                created_count += 1
                self.stdout.write(
                    f'✅ Reseña creada: {appointment.patient.get_full_name()} → '
                    f'{appointment.psychologist.get_full_name()}: {rating}/5 estrellas'
                )
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error creando reseña para cita {appointment.id}: {e}')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n🎉 Se crearon {created_count} reseñas exitosamente!')
        )
        
        # Mostrar estadísticas actualizadas
        self.stdout.write('\n📊 Estadísticas actualizadas:')
        from apps.professionals.models import ProfessionalProfile
        
        for profile in ProfessionalProfile.objects.filter(reviews__isnull=False).distinct():
            self.stdout.write(
                f'  • {profile.user.get_full_name()}: {profile.average_rating}/5.0 '
                f'({profile.total_reviews} reseñas)'
            )