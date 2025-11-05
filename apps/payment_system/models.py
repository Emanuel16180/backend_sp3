# apps/payment_system/models.py

from django.db import models
from django.conf import settings
from apps.appointments.models import Appointment

class PaymentTransaction(models.Model):
    """
    Modelo para registrar las transacciones de pago
    """
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('completed', 'Completado'),
        ('failed', 'Fallido'),
        ('cancelled', 'Cancelado'),
        ('refunded', 'Reembolsado'),
    ]
    
    # Relaciones
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.SET_NULL,
        related_name='payment_transaction',
        null=True,
        blank=True
    )
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payment_transactions'
    )
    
    # Información de Stripe
    stripe_session_id = models.CharField(max_length=255, unique=True)
    stripe_payment_intent_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Información del pago
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Información adicional
    stripe_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    net_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    class Meta:
        db_table = 'payment_transactions'
        verbose_name = 'Transacción de Pago'
        verbose_name_plural = 'Transacciones de Pago'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Pago {self.stripe_session_id} - {self.amount} {self.currency}"

from apps.professionals.models import CarePlan

class PatientPlan(models.Model):
    """
    Modelo que vincula a un Paciente con un Plan de Cuidado (CU-44)
    que ha comprado.
    """
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='purchased_plans',
        limit_choices_to={'user_type': 'patient'}
    )
    plan = models.ForeignKey(
        CarePlan,
        on_delete=models.CASCADE,
        related_name='purchases'
    )
    # Vinculamos la transacción de Stripe
    transaction = models.OneToOneField(
        PaymentTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='patient_plan'
    )
    
    total_sessions = models.PositiveIntegerField()
    # Este campo es clave: cuenta cuántas sesiones ha usado
    sessions_used = models.PositiveIntegerField(default=0) 
    
    is_active = models.BooleanField(default=True)
    purchased_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Plan Adquirido por Paciente'
        verbose_name_plural = 'Planes Adquiridos'

    def __str__(self):
        return f"Plan '{self.plan.title}' de {self.patient.get_full_name()} ({self.sessions_used}/{self.total_sessions} usadas)"
    
    @property
    def sessions_remaining(self):
        return self.total_sessions - self.sessions_used
