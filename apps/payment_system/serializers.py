# apps/payment_system/serializers.py
import stripe
from rest_framework import serializers
from django.conf import settings
from .models import PaymentTransaction, PatientPlan
from apps.appointments.models import Appointment
from apps.professionals.serializers import CarePlanSerializer

class PaymentTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar el historial de pagos de un paciente.
    """
    # Añadimos campos legibles desde la cita relacionada
    psychologist_name = serializers.CharField(source='appointment.psychologist.get_full_name', read_only=True)
    appointment_date = serializers.DateField(source='appointment.appointment_date', read_only=True)
    appointment_time = serializers.TimeField(source='appointment.start_time', read_only=True)

    class Meta:
        model = PaymentTransaction
        fields = [
            'id', 
            'appointment_date',
            'appointment_time',
            'psychologist_name', 
            'amount', 
            'currency', 
            'status', 
            'paid_at', 
            'stripe_session_id'
        ]
        read_only_fields = fields # Este endpoint es solo de lectura

class PaymentConfirmationSerializer(serializers.Serializer):
    """
    Serializer para confirmar un pago usando el ID de la sesión de Stripe.
    """
    session_id = serializers.CharField(max_length=255)

    def validate(self, data):
        session_id = data.get('session_id')
        
        try:
            # 1. Validamos la sesión con Stripe
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status != 'paid':
                raise serializers.ValidationError("El pago no ha sido completado.")
            
            # 2. Obtenemos la cita de los metadatos
            metadata = session.get('metadata', {})
            appointment_id = metadata.get('appointment_id')
            if not appointment_id:
                raise serializers.ValidationError("ID de cita no encontrado en la sesión de Stripe.")
            
            # 3. Buscamos la cita en nuestra BD
            appointment = Appointment.objects.get(id=appointment_id)
            
            # 4. ¡LA CLAVE! Guardamos todo en validated_data para que la vista lo use
            data['stripe_session'] = session
            data['appointment'] = appointment
            
            return data
        
        except Appointment.DoesNotExist:
            raise serializers.ValidationError("La cita asociada a este pago no fue encontrada.")
        except stripe.error.StripeError as e:
            raise serializers.ValidationError(f"Error de Stripe: {str(e)}")
        except Exception as e:
            raise serializers.ValidationError(f"Error validando la sesión: {str(e)}")

class PaymentReportSerializer(serializers.ModelSerializer):
    """
    Serializer para el reporte de pagos (Vista de Admin).
    Calcula las ganancias de la clínica y del profesional.
    """
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    psychologist_name = serializers.CharField(source='appointment.psychologist.get_full_name', read_only=True)
    
    # Nuevos campos calculados
    clinic_earning = serializers.SerializerMethodField()
    psychologist_earning = serializers.SerializerMethodField()
    clinic_percentage = serializers.SerializerMethodField()

    class Meta:
        model = PaymentTransaction
        fields = [
            'id', 
            'paid_at', 
            'patient_name', 
            'psychologist_name', 
            'amount',
            'clinic_percentage',
            'clinic_earning',
            'psychologist_earning',
            'status',
            'currency',
        ]
    
    def get_clinic_percentage(self, obj):
        # Obtenemos el porcentaje desde el "contexto" que le pasará la vista
        return self.context.get('clinic_percentage', 0)

    def get_clinic_earning(self, obj):
        percentage = self.context.get('clinic_percentage', 0)
        return (obj.amount * percentage) / 100

    def get_psychologist_earning(self, obj):
        clinic_earning = self.get_clinic_earning(obj)
        return obj.amount - clinic_earning


class PatientPlanSerializer(serializers.ModelSerializer):
    """Serializer para mostrar los planes que un paciente ha comprado."""
    plan = CarePlanSerializer(read_only=True)
    sessions_remaining = serializers.IntegerField(read_only=True)

    class Meta:
        model = PatientPlan
        fields = [
            'id',
            'plan',
            'total_sessions',
            'sessions_used',
            'sessions_remaining',
            'is_active',
            'purchased_at'
        ]