# apps/professionals/models.py

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg
from django.conf import settings

User = get_user_model()

class Specialization(models.Model):
    """
    Especialidades de los profesionales
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'specializations'
        verbose_name = 'Especialización'
        verbose_name_plural = 'Especializaciones'
    
    def __str__(self):
        return self.name


class ProfessionalProfile(models.Model):
    """
    Perfil profesional para psicólogos
    """
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='professional_profile'
    )
    license_number = models.CharField(max_length=50, unique=True)
    specializations = models.ManyToManyField(Specialization, blank=True)
    bio = models.TextField(help_text="Descripción profesional")
    education = models.TextField(help_text="Formación académica")
    experience_years = models.PositiveIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(50)],
        help_text="Años de experiencia"
    )
    consultation_fee = models.DecimalField(
        max_digits=8, 
        decimal_places=2,
        help_text="Tarifa por consulta en Bs."
    )
    
    # Configuración de consultas
    session_duration = models.PositiveIntegerField(
        default=60, 
        help_text="Duración de sesión en minutos"
    )
    accepts_online_sessions = models.BooleanField(default=True)
    accepts_in_person_sessions = models.BooleanField(default=True)
    
    # Información de ubicación
    office_address = models.TextField(blank=True)
    city = models.CharField(max_length=50, blank=True)
    state = models.CharField(max_length=50, blank=True, default="La Paz")
    
    # Calificaciones y reseñas
    average_rating = models.DecimalField(
        max_digits=3, 
        decimal_places=2, 
        default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    total_reviews = models.PositiveIntegerField(default=0)
    
    # Estado del perfil
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    profile_completed = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'professional_profiles'
        verbose_name = 'Perfil Profesional'
        verbose_name_plural = 'Perfiles Profesionales'
    
    def __str__(self):
        return f"Dr. {self.user.get_full_name()}"

    def update_rating(self):
        """
        Calcula y actualiza la calificación promedio y el total de reseñas.
        """
        reviews = self.reviews.all()
        self.total_reviews = reviews.count()

        if self.total_reviews > 0:
            # Calcula el promedio de la columna 'rating'
            average = reviews.aggregate(Avg('rating'))['rating__avg']
            self.average_rating = round(average, 2)
        else:
            self.average_rating = 0.00

        self.save(update_fields=['average_rating', 'total_reviews'])


class WorkingHours(models.Model):
    """
    Horarios de trabajo de los profesionales
    """
    DAYS_OF_WEEK = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    
    professional = models.ForeignKey(
        ProfessionalProfile, 
        on_delete=models.CASCADE,
        related_name='working_hours'
    )
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'working_hours'
        verbose_name = 'Horario de Trabajo'
        verbose_name_plural = 'Horarios de Trabajo'
        unique_together = ['professional', 'day_of_week']
    
    def __str__(self):
        return f"{self.professional} - {self.get_day_of_week_display()}: {self.start_time} - {self.end_time}"


class Review(models.Model):
    """
    Modelo para una calificación y comentario dejado por un paciente
    sobre un profesional después de una cita.
    """
    professional = models.ForeignKey(
        ProfessionalProfile,
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews_given'
    )
    appointment = models.OneToOneField(
        'appointments.Appointment', # Usamos un string para evitar importación circular
        on_delete=models.CASCADE,
        related_name='review',
        help_text="La cita específica que se está calificando."
    )

    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reviews'
        ordering = ['-created_at']
        unique_together = ('appointment', 'patient') # Un paciente solo puede calificar una cita una vez
        verbose_name = 'Reseña'
        verbose_name_plural = 'Reseñas'

    def __str__(self):
        return f'Calificación de {self.patient.get_full_name()} para {self.professional.user.get_full_name()}: {self.rating} estrellas'

    def save(self, *args, **kwargs):
        """
        Sobrescribimos save para recalcular el rating del profesional.
        """
        super().save(*args, **kwargs)
        # Después de guardar la reseña, actualizamos el perfil del profesional
        self.professional.update_rating()

    def delete(self, *args, **kwargs):
        """
        Sobrescribimos delete para recalcular el rating del profesional.
        """
        professional = self.professional
        super().delete(*args, **kwargs)
        professional.update_rating()

class VerificationDocument(models.Model):
    """
    Documentos subidos por un profesional para verificar su perfil.
    """
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('approved', 'Aprobado'),
        ('rejected', 'Rechazado'),
    ]

    professional = models.ForeignKey(
        ProfessionalProfile,
        on_delete=models.CASCADE,
        related_name='verification_documents'
    )
    description = models.CharField(max_length=255, blank=True)
    
    # Usamos un TextField para guardar la URL pública de Supabase
    file_url = models.TextField() 
    
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    # Campo opcional para que el admin deje notas
    admin_notes = models.TextField(blank=True) 

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Documento de Verificación'
        verbose_name_plural = 'Documentos de Verificación'

    def __str__(self):
        return f"Documento de {self.professional.user.get_full_name()} ({self.status})"

class CarePlan(models.Model):
    """
    Modelo para Paquetes o Planes de Cuidado (CU-44)
    Creado por un psicólogo.
    """
    psychologist = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='care_plans',
        limit_choices_to={'user_type': 'professional'}
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    number_of_sessions = models.PositiveIntegerField(default=1)
    
    # Precio total del paquete
    total_price = models.DecimalField(max_digits=10, decimal_places=2) 
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Plan de Cuidado'
        verbose_name_plural = 'Planes de Cuidado'

    def __str__(self):
        return f"{self.title} ({self.number_of_sessions} sesiones) - {self.psychologist.get_full_name()}"