# apps/appointments/models.py

from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta

class PsychologistAvailability(models.Model):
    """
    Define los horarios disponibles de cada psicólogo
    """
    WEEKDAYS = [
        (0, 'Lunes'),
        (1, 'Martes'),
        (2, 'Miércoles'),
        (3, 'Jueves'),
        (4, 'Viernes'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    
    psychologist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='availabilities',
        limit_choices_to={'user_type': 'professional'}
    )
    weekday = models.IntegerField(choices=WEEKDAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)
    
    # Para bloqueos específicos (vacaciones, etc)
    blocked_dates = models.JSONField(default=list, blank=True)  # Lista de fechas bloqueadas
    
    class Meta:
        unique_together = ['psychologist', 'weekday', 'start_time']
        ordering = ['weekday', 'start_time']
        verbose_name = 'Disponibilidad'
        verbose_name_plural = 'Disponibilidades'
    
    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError('La hora de inicio debe ser menor que la hora de fin')
    
    def __str__(self):
        return f"{self.psychologist.get_full_name()} - {self.get_weekday_display()} {self.start_time}-{self.end_time}"


class Appointment(models.Model):
    """
    Modelo para las citas entre pacientes y psicólogos
    """
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('confirmed', 'Confirmada'),
        ('cancelled', 'Cancelada'),
        ('completed', 'Completada'),
        ('no_show', 'No asistió'),
    ]
    
    APPOINTMENT_TYPE = [
        ('online', 'En línea'),
        ('in_person', 'Presencial'),
    ]
    
    # Relaciones principales
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='patient_appointments',
        limit_choices_to={'user_type': 'patient'}
    )
    psychologist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='psychologist_appointments',
        limit_choices_to={'user_type': 'professional'}
    )
    
    # Información de la cita
    appointment_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    appointment_type = models.CharField(
        max_length=20,
        choices=APPOINTMENT_TYPE,
        default='in_person'
    )
    
    # Estado y detalles
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    reason_for_visit = models.TextField(
        blank=True,
        help_text="Motivo de la consulta"
    )
    notes = models.TextField(
        blank=True,
        help_text="Notas adicionales"
    )
    
    # Información de pago
    consultation_fee = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    is_paid = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Para videollamadas
    meeting_link = models.URLField(blank=True, null=True)
    
    class Meta:
        ordering = ['-appointment_date', '-start_time']
        unique_together = ['psychologist', 'appointment_date', 'start_time']
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'
    
    def clean(self):
        # Validar que no sea en el pasado
        if self.appointment_date < timezone.now().date():
            raise ValidationError('No se pueden agendar citas en fechas pasadas')
        
        # Validar que el horario esté dentro de la disponibilidad del psicólogo
        if not self.is_within_availability():
            raise ValidationError('El psicólogo no está disponible en este horario')
        
        # Validar que no haya conflictos con otras citas
        if self.has_conflict():
            raise ValidationError('Ya existe una cita en este horario')
    
    def is_within_availability(self):
        """Verifica si la cita está dentro del horario disponible del psicólogo"""
        weekday = self.appointment_date.weekday()
        
        # Verificar si la fecha está bloqueada
        availabilities = self.psychologist.availabilities.filter(
            weekday=weekday,
            is_active=True
        )
        
        for availability in availabilities:
            # Verificar si la fecha específica está bloqueada
            if str(self.appointment_date) in availability.blocked_dates:
                return False
            
            # Verificar si el horario está dentro del rango disponible
            if (availability.start_time <= self.start_time and 
                self.end_time <= availability.end_time):
                return True
        
        return False
    
    def has_conflict(self):
        """Verifica si hay conflicto con otras citas"""
        return Appointment.objects.filter(
            psychologist=self.psychologist,
            appointment_date=self.appointment_date,
            status__in=['pending', 'confirmed']
        ).exclude(pk=self.pk).filter(
            models.Q(start_time__lt=self.end_time) & 
            models.Q(end_time__gt=self.start_time)
        ).exists()
    
    def save(self, *args, **kwargs):
        # Auto-calcular hora de fin basado en la duración de sesión del psicólogo
        if not self.end_time and hasattr(self.psychologist, 'professional_profile'):
            duration = self.psychologist.professional_profile.session_duration
            start_datetime = datetime.combine(self.appointment_date, self.start_time)
            end_datetime = start_datetime + timedelta(minutes=duration)
            self.end_time = end_datetime.time()
        
        # Establecer el precio de consulta
        if not self.consultation_fee and hasattr(self.psychologist, 'professional_profile'):
            self.consultation_fee = self.psychologist.professional_profile.consultation_fee
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.patient.get_full_name()} con {self.psychologist.get_full_name()} - {self.appointment_date} {self.start_time}"


class TimeSlot(models.Model):
    """
    Modelo auxiliar para generar slots de tiempo disponibles
    """
    psychologist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='time_slots'
    )
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['psychologist', 'date', 'start_time']
        ordering = ['date', 'start_time']
    
    def __str__(self):
        return f"{self.psychologist.get_full_name()} - {self.date} {self.start_time}-{self.end_time}"


class Referral(models.Model):
    """
    Modelo para gestionar la derivación de una cita de un 
    profesional a otro.
    """
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('accepted', 'Aceptada'),
        ('rejected', 'Rechazada'),
    ]

    # La cita que se está derivando
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name='referral'
    )
    
    # Quién la deriva
    referring_psychologist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='referrals_made',
        limit_choices_to={'user_type': 'professional'}
    )
    
    # A quién se deriva
    referred_psychologist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='referrals_received',
        limit_choices_to={'user_type': 'professional'}
    )
    
    reason = models.TextField(help_text="Motivo de la derivación.")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Derivación'
        verbose_name_plural = 'Derivaciones'

    def __str__(self):
        return f"Derivación de Cita {self.appointment_id} a {self.referred_psychologist.get_full_name()}"