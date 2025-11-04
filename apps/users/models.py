# apps/users/models.py

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.core.validators import RegexValidator

class CustomUserManager(BaseUserManager):
    """
    Manager personalizado para el modelo CustomUser
    """
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        
        # Generar username automáticamente si no se proporciona
        if 'username' not in extra_fields:
            extra_fields['username'] = email.split('@')[0]
        
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('user_type', 'admin')
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('El superuser debe tener is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('El superuser debe tener is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractUser):
    """
    Modelo de usuario personalizado para Centro de Salud Mental
    CU-01: Registrarse en el Sistema
    CU-05: Gestionar Perfil Personal
    """
    USER_TYPES = (
        ('patient', 'Paciente'),
        ('professional', 'Psicólogo'),
        ('admin', 'Administrador'),
    )
    
    GENDER_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
    ]
    
    # Campos básicos requeridos
    email = models.EmailField(unique=True, verbose_name='Email')
    user_type = models.CharField(
        max_length=15, 
        choices=USER_TYPES, 
        default='patient',
        verbose_name='Tipo de usuario'
    )
    
    # Campos adicionales para pacientes y profesionales (opcionales para admin)
    ci = models.CharField(
        max_length=15, 
        unique=True,
        validators=[RegexValidator(r'^\d{7,10}$', 'CI debe tener entre 7-10 dígitos')],
        verbose_name='Cédula de Identidad',
        help_text='Cédula de identidad sin guiones ni puntos',
        null=True, blank=True
    )
    phone = models.CharField(
        max_length=15, 
        validators=[RegexValidator(r'^\d{7,8}$', 'Teléfono debe tener 7-8 dígitos')],
        verbose_name='Teléfono',
        null=True, blank=True
    )
    gender = models.CharField(
        max_length=1, 
        choices=GENDER_CHOICES,
        verbose_name='Sexo',
        null=True, blank=True
    )
    address = models.TextField(verbose_name='Dirección', blank=True)
    date_of_birth = models.DateField(verbose_name='Fecha de nacimiento', null=True, blank=True)
    
    # Campos opcionales
    profile_picture = models.ImageField(
        upload_to='profile_pictures/', 
        blank=True, 
        null=True,
        verbose_name='Foto de perfil'
    )
    
    # Control de estado
    is_verified = models.BooleanField(default=False, verbose_name='Verificado')
    is_active_patient = models.BooleanField(default=True, verbose_name='Paciente activo')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Configuración del modelo
    objects = CustomUserManager()
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']
    
    class Meta:
        db_table = 'users'
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
    
    def __str__(self):
        if self.ci:
            return f"{self.get_full_name()} (CI: {self.ci})"
        return f"{self.get_full_name()} ({self.email})"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    @property
    def age(self):
        """Calcular edad del paciente"""
        if not self.date_of_birth:
            return None
        from datetime import date
        today = date.today()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    def save(self, *args, **kwargs):
        if not self.username:
            # Si no hay username, lo generamos a partir del email
            # para evitar errores de unicidad.
            self.username = self.email.split('@')[0]
        super().save(*args, **kwargs)


class PatientProfile(models.Model):
    """
    Perfil adicional simple para pacientes del centro de salud mental
    CU-05: Gestionar Perfil Personal
    """
    user = models.OneToOneField(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='patient_profile'
    )
    
    # Contacto de emergencia (obligatorio)
    emergency_contact_name = models.CharField(
        max_length=100, 
        verbose_name='Nombre contacto de emergencia',
        blank=True
    )
    emergency_contact_phone = models.CharField(
        max_length=15,
        validators=[RegexValidator(r'^\d{7,8}$', 'Teléfono debe tener 7-8 dígitos')],
        verbose_name='Teléfono contacto de emergencia',
        blank=True
    )
    emergency_contact_relationship = models.CharField(
        max_length=50,
        verbose_name='Parentesco',
        help_text='Ej: Madre, Esposo, Hermana, etc.',
        blank=True
    )
    
    # Información básica adicional
    occupation = models.CharField(
        max_length=100, 
        blank=True,
        verbose_name='Ocupación'
    )
    education_level = models.CharField(
        max_length=50,
        choices=[
            ('primaria', 'Primaria'),
            ('secundaria', 'Secundaria'),
            ('tecnico', 'Técnico'),
            ('universitario', 'Universitario'),
            ('postgrado', 'Postgrado'),
        ],
        blank=True,
        verbose_name='Nivel educativo'
    )
    
    # Motivo de consulta inicial
    initial_reason = models.TextField(
        blank=True,
        verbose_name='Motivo inicial de consulta',
        help_text='Descripción breve del motivo de la primera consulta'
    )
    
    # Referencias
    how_found_us = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='¿Cómo nos encontró?',
        help_text='Referido por médico, internet, familiar, etc.'
    )
    
    # Estado del perfil
    profile_completed = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'patient_profiles'
        verbose_name = 'Perfil de Paciente'
        verbose_name_plural = 'Perfiles de Pacientes'
    
    def __str__(self):
        return f"Perfil de {self.user.get_full_name()}"