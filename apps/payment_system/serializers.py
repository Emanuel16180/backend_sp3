# apps/payment_system/serializers.py
import stripe
from rest_framework import serializers
from django.conf import settings
from .models import PaymentTransaction, PatientPlan
from apps.appointments.models import Appointment
from apps.professionals.serializers import CarePlanSerializer
from apps.professionals.models import CarePlan

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
            
            # 2. Obtenemos la metadata
            metadata = session.get('metadata', {})
            appointment_id = metadata.get('appointment_id')
            plan_id = metadata.get('plan_id') # <-- AÑADIDO: Buscar el plan_id
            
            # 3. ¡LA CLAVE! Guardamos la sesión
            data['stripe_session'] = session
            
            if appointment_id:
                # --- Caso 1: Es un pago de Cita Única ---
                appointment = Appointment.objects.get(id=appointment_id)
                data['appointment'] = appointment # Guardamos la cita
            
            elif plan_id:
                # --- Caso 2: Es un pago de Plan ---
                plan = CarePlan.objects.get(id=plan_id)
                data['plan'] = plan # Guardamos el plan
            
            else:
                # --- Caso de Error ---
                raise serializers.ValidationError(
                    "ID de cita o plan no encontrado en la sesión de Stripe."
                )
            
            return data
        
        except Appointment.DoesNotExist:
            raise serializers.ValidationError("La cita asociada a este pago no fue encontrada.")
        except CarePlan.DoesNotExist: # <-- AÑADIDO: Manejar error de plan
            raise serializers.ValidationError("El plan asociado a este pago no fue encontrado.")
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
    psychologist_name = serializers.SerializerMethodField()
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
    
    def get_psychologist_name(self, obj):
        """
        Obtiene el nombre del psicólogo, ya sea desde la cita
        o desde el plan comprado.
        """
        try:
            if obj.appointment:
                # Caso 1: Es un pago de Cita
                return obj.appointment.psychologist.get_full_name()
            elif hasattr(obj, 'patient_plan') and obj.patient_plan:
                # Caso 2: Es un pago de Plan (obj.patient_plan es la relación)
                return obj.patient_plan.plan.psychologist.get_full_name()
        except AttributeError:
            # En caso de que algo se haya borrado (ej. el psicólogo)
            return "Psicólogo no disponible"
        
        return "N/A (Pago no asociado)"

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

class PsychologistPaymentSerializer(serializers.ModelSerializer):
    """
    Serializer para que el psicólogo vea su historial de ingresos.
    Muestra cuánto ganó él (neto) y quién le pagó.
    """
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    service_type = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    your_earning = serializers.SerializerMethodField()

    class Meta:
        model = PaymentTransaction
        fields = [
            'id',
            'paid_at',
            'patient_name',
            'amount',          # Monto total cobrado al paciente
            'your_earning',    # Lo que recibe el psicólogo
            'service_type',    # "Cita" o "Plan"
            'description',     # Detalles
            'status'
        ]

    def get_service_type(self, obj):
        if obj.appointment:
            return "Cita Individual"
        elif hasattr(obj, 'patient_plan') and obj.patient_plan:
            return "Plan de Cuidado"
        return "Otro"

    def get_description(self, obj):
        if obj.appointment:
            return f"Cita del {obj.appointment.appointment_date}"
        elif hasattr(obj, 'patient_plan') and obj.patient_plan:
            return f"Plan: {obj.patient_plan.plan.title}"
        return "Pago de servicio"

    def get_your_earning(self, obj):
        # Obtenemos el % de la clínica desde el contexto o usamos un default (ej: 25%)
        # Nota: Lo ideal es sacar esto del modelo Clinic, pero para visualizar rápido:
        clinic_fee_percentage = 25 # Puedes ajustar esto o pasarlo por contexto
        
        # Ganancia del psicólogo = Total - Comisión Clínica
        clinic_cut = (obj.amount * clinic_fee_percentage) / 100
        return obj.amount - clinic_cut