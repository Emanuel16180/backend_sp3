# apps/clinical_history/models.py

from django.db import models
from django.conf import settings
from apps.appointments.models import Appointment
from .storage import ClinicalDocumentS3Storage
from datetime import date

class SessionNote(models.Model):
    """
    Modelo para las notas privadas de un profesional sobre una cita específica.
    """
    # Usamos OneToOne para asegurar que solo haya UNA nota por cita.
    appointment = models.OneToOneField(
        Appointment, 
        on_delete=models.CASCADE, 
        related_name='session_note'
    )
    
    content = models.TextField(
        help_text="Notas privadas del profesional sobre la sesión."
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-appointment__appointment_date']
        verbose_name = 'Nota de Sesión'
        verbose_name_plural = 'Notas de Sesión'
        db_table = 'session_notes'

    def __str__(self):
        return f"Nota para la cita del {self.appointment.appointment_date} con {self.appointment.patient.get_full_name()}"


class ClinicalDocument(models.Model):
    """
    Modelo para documentos subidos por un profesional para un paciente específico.
    """
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='clinical_documents',
        limit_choices_to={'user_type': 'patient'}
    )
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # Si el psicólogo se elimina, no borramos el documento
        null=True,
        related_name='uploaded_documents',
        limit_choices_to={'user_type': 'professional'}
    )
    
    # El archivo en S3
    file = models.FileField(
        upload_to='clinical_documents/%Y/%m/%d/',
        storage='apps.clinical_history.storage.ClinicalDocumentS3Storage'
    )
    
    description = models.CharField(max_length=255, help_text="Descripción o título del documento.")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Documento Clínico'
        verbose_name_plural = 'Documentos Clínicos'
        db_table = 'clinical_documents'

    def __str__(self):
        return f"Documento '{self.description}' para {self.patient.get_full_name()}"


# --- 👇 AÑADIDO: NUEVO MODELO PARA HISTORIAL CLÍNICO COMPLETO 👇 ---

class ClinicalHistory(models.Model):
    """
    Modelo central para almacenar el historial clínico completo de un paciente.
    """
    # --- VÍNCULO CON EL PACIENTE ---
    patient = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='clinical_history',
        limit_choices_to={'user_type': 'patient'},
        primary_key=True # Cada paciente tendrá solo UNA historia clínica
    )

    # --- SECCIONES DEL HISTORIAL ---

    # Motivo e Historia
    consultation_reason = models.TextField(blank=True, help_text="Frase textual del paciente sobre el motivo de consulta.")
    history_of_illness = models.TextField(blank=True, help_text="Relato cronológico de la enfermedad actual (HEA).")

    # Antecedentes
    personal_pathological_history = models.TextField(blank=True, help_text="Enfermedades previas, cirugías, trastornos mentales, etc.")
    family_history = models.TextField(blank=True, help_text="Trastornos mentales, suicidio, adicciones en la familia.")
    personal_non_pathological_history = models.JSONField(default=dict, blank=True, help_text="Hábitos de alimentación, sueño, consumo de sustancias, etc.")

    # Examen / Exploración
    mental_examination = models.JSONField(default=dict, blank=True, help_text="Resultados de la exploración mental (conciencia, orientación, lenguaje, etc.).")
    complementary_tests = models.TextField(blank=True, help_text="Resultados de pruebas de laboratorio, gabinete o psicométricas.")

    # Diagnóstico y Plan
    diagnoses = models.JSONField(default=list, blank=True, help_text="Lista de diagnósticos (principal y secundarios) con códigos CIE-10/DSM-5.")
    therapeutic_plan = models.JSONField(default=dict, blank=True, help_text="Plan farmacológico, psicoterapéutico e intervenciones sociales.")

    # Riesgos y Alertas
    risk_assessment = models.JSONField(default=dict, blank=True, help_text="Evaluación de riesgos (autolesión, heteroagresión, recaída).")
    sensitive_topics = models.TextField(blank=True, help_text="Temas delicados a tratar con cuidado.")

    # --- METADATOS ---
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_histories',
        help_text="Profesional que creó el historial."
    )
    last_updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_histories',
        help_text="Último profesional que actualizó el historial."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Historial Clínico'
        verbose_name_plural = 'Historiales Clínicos'

    def __str__(self):
        return f"Historial Clínico de {self.patient.get_full_name()}"

# apps/clinical_history/models.py
# ... (después de la clase ClinicalHistory) ...

class InitialTriage(models.Model):
    """
    Modelo para almacenar los resultados del triaje inicial (CU-21)
    de un paciente.
    """
    patient = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='initial_triage',
        limit_choices_to={'user_type': 'patient'},
        primary_key=True # Cada paciente solo tiene un triaje inicial
    )
    
    # Almacenamos todas las respuestas del formulario
    answers = models.JSONField(
        default=dict,
        help_text="JSON con las preguntas y respuestas del árbol de triaje."
    )
    
    # El resultado final y la recomendación
    pre_diagnosis = models.CharField(
        max_length=255,
        blank=True,
        help_text="Diagnóstico preliminar basado en el triaje."
    )
    recommendation = models.TextField(
        blank=True,
        help_text="Recomendación generada por el sistema."
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Triaje Inicial'
        verbose_name_plural = 'Triajes Iniciales'

    def __str__(self):
        return f"Triaje de {self.patient.get_full_name()} - {self.pre_diagnosis}"


class MoodJournal(models.Model):
    """
    Modelo para el Diario de Estado de Ánimo (CU-41).
    Registra una entrada de ánimo por paciente, por día.
    """
    MOOD_CHOICES = [
        ('feliz', 'Feliz'),
        ('triste', 'Triste'),
        ('ansioso', 'Ansioso/a'),
        ('enojado', 'Enojado/a'),
        ('neutral', 'Neutral'),
        ('cansado', 'Cansado/a'),
    ]

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mood_journals',
        limit_choices_to={'user_type': 'patient'}
    )
    
    # Usamos date.today para registrar el día
    date = models.DateField(default=date.today)
    
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES)
    
    notes = models.TextField(
        blank=True, 
        null=True,
        help_text="Notas adicionales sobre el estado de ánimo."
    )
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date']
        verbose_name = 'Entrada de Ánimo'
        verbose_name_plural = 'Diario de Ánimos'
        
        # --- ¡ESTA ES LA CLAVE! ---
        # Asegura que un paciente solo pueda tener UNA entrada por día.
        unique_together = ('patient', 'date')

    def __str__(self):
        return f"{self.patient.get_full_name()} - {self.date}: {self.get_mood_display()}"

class Objective(models.Model):
    """
    Modelo para los Objetivos terapéuticos (CU-46)
    Asignado por un psicólogo a un paciente.
    """
    STATUS_CHOICES = [
        ('active', 'Activo'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ]

    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='objectives',
        limit_choices_to={'user_type': 'patient'}
    )
    psychologist = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='assigned_objectives',
        limit_choices_to={'user_type': 'professional'}
    )
    # Vinculado a la cita donde se asignó
    appointment = models.ForeignKey(
        'appointments.Appointment',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='objectives'
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Objetivo Terapéutico'
        verbose_name_plural = 'Objetivos Terapéuticos'

    def __str__(self):
        return f"Objetivo para {self.patient.get_full_name()}: {self.title}"


class Task(models.Model):
    """
    Modelo para las Tareas específicas (CU-46)
    Vinculadas a un Objetivo.
    """
    RECURRENCE_CHOICES = [
        ('once', 'Una vez'),
        ('daily', 'Diaria'),
        ('weekly', 'Semanal'),
    ]

    objective = models.ForeignKey(
        Objective,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    title = models.CharField(max_length=255)
    recurrence = models.CharField(max_length=10, choices=RECURRENCE_CHOICES, default='daily')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = 'Tarea'
        verbose_name_plural = 'Tareas'

    def __str__(self):
        return f"[{self.get_recurrence_display()}] {self.title}"


class TaskCompletion(models.Model):
    """
    Modelo para registrar cuándo un paciente completa una tarea (CU-47)
    """
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name='completions'
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='task_completions'
    )
    completed_date = models.DateField(default=date.today)
    notes = models.TextField(blank=True, null=True, help_text="Notas opcionales del paciente.")

    class Meta:
        ordering = ['-completed_date']
        verbose_name = 'Tarea Completada'
        verbose_name_plural = 'Tareas Completadas'
        
        # ¡Clave! Un paciente solo puede completar una tarea una vez por día.
        unique_together = ('task', 'patient', 'completed_date')
