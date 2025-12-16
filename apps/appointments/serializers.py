# apps/appointments/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Appointment, PsychologistAvailability, TimeSlot
from apps.professionals.serializers import ProfessionalProfileSerializer
from datetime import datetime, timedelta
from apps.payment_system.models import PatientPlan

User = get_user_model()


class PsychologistAvailabilitySerializer(serializers.ModelSerializer):
    psychologist_name = serializers.CharField(source='psychologist.get_full_name', read_only=True)
    weekday_display = serializers.CharField(source='get_weekday_display', read_only=True)
    
    class Meta:
        model = PsychologistAvailability
        fields = [
            'id', 'psychologist', 'psychologist_name', 'weekday', 
            'weekday_display', 'start_time', 'end_time', 'is_active',
            'blocked_dates'
        ]
        read_only_fields = ['id', 'psychologist_name', 'weekday_display']
    
    def validate(self, data):
        if data.get('start_time') and data.get('end_time'):
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError(
                    "La hora de inicio debe ser menor que la hora de fin"
                )
        return data


class TimeSlotSerializer(serializers.ModelSerializer):
    psychologist_name = serializers.CharField(source='psychologist.get_full_name', read_only=True)
    
    class Meta:
        model = TimeSlot
        fields = ['id', 'psychologist', 'psychologist_name', 'date', 
                  'start_time', 'end_time', 'is_available']
        read_only_fields = ['id', 'psychologist_name']


class AppointmentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.get_full_name', read_only=True)
    psychologist_name = serializers.CharField(source='psychologist.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    appointment_type_display = serializers.CharField(source='get_appointment_type_display', read_only=True)
    
    class Meta:
        model = Appointment
        fields = [
            'id', 'patient', 'patient_name', 'psychologist', 'psychologist_name',
            'appointment_date', 'start_time', 'end_time', 'appointment_type',
            'appointment_type_display', 'status', 'status_display',
            'reason_for_visit', 'notes', 'consultation_fee', 'is_paid',
            'meeting_link', 'created_at', 'updated_at', 'patient_plan'
        ]
        read_only_fields = [
            'id', 'patient_name', 'psychologist_name', 'status_display',
            'appointment_type_display', 'created_at', 'updated_at', 'end_time',
            'consultation_fee', 'patient_plan'
        ]
    
   # En apps/appointments/serializers.py, dentro de class AppointmentSerializer:

    def validate(self, data):
        # Validar que la fecha no sea pasada
        if 'appointment_date' in data:
            if data['appointment_date'] < datetime.now().date():
                raise serializers.ValidationError(
                    "No se pueden agendar citas en fechas pasadas"
                )

        # Validar disponibilidad del psicólogo
        psychologist = data.get('psychologist')
        appointment_date = data.get('appointment_date')
        start_time = data.get('start_time')

        if psychologist and appointment_date and start_time:
            calculated_end_time = None # <-- Definimos la variable aquí
            
            # Calcular end_time basado en la duración de sesión
            if hasattr(psychologist, 'professional_profile'):
                duration = psychologist.professional_profile.session_duration
                start_datetime = datetime.combine(appointment_date, start_time)
                end_datetime = start_datetime + timedelta(minutes=duration)
                calculated_end_time = end_datetime.time()
                data['end_time'] = calculated_end_time # Lo añadimos a los datos

            if not calculated_end_time:
                # Si no se pudo calcular la hora de fin, detenemos la validación
                raise serializers.ValidationError("No se pudo determinar la duración de la sesión.")
            
            # Verificar disponibilidad
            weekday = appointment_date.weekday()
            availability = PsychologistAvailability.objects.filter(
                psychologist=psychologist,
                weekday=weekday,
                is_active=True,
                start_time__lte=start_time,
                end_time__gte=calculated_end_time # <-- Usamos la variable calculada
            ).first()
            
            if not availability:
                raise serializers.ValidationError(
                    "El psicólogo no está disponible en este horario"
                )
            
            # Verificar si la fecha está bloqueada
            if str(appointment_date) in availability.blocked_dates:
                raise serializers.ValidationError(
                    "El psicólogo no está disponible en esta fecha"
                )
            
            # Verificar conflictos con otras citas
            conflicting_appointments = Appointment.objects.filter(
                psychologist=psychologist,
                appointment_date=appointment_date,
                status__in=['pending', 'confirmed']
            ).filter(
                start_time__lt=calculated_end_time, # <-- Usamos la variable calculada
                end_time__gt=start_time
            )
            
            if self.instance:
                conflicting_appointments = conflicting_appointments.exclude(pk=self.instance.pk)
            
            if conflicting_appointments.exists():
                raise serializers.ValidationError(
                    "Ya existe una cita en este horario"
                )
        
        return data

class AppointmentCreateSerializer(serializers.ModelSerializer):
    """Serializer específico para crear citas (ahora con lógica de Planes)"""

    appointment_type = serializers.CharField(default='in_person', required=False)

    # --- 👇 NUEVO CAMPO OPCIONAL 👇 ---
    # El frontend debe enviar el ID del plan que quiere usar
    patient_plan_id = serializers.IntegerField(required=False, write_only=True, allow_null=True)

    class Meta:
        model = Appointment
        fields = [
            'psychologist', 'appointment_date', 'start_time',
            'appointment_type', 'reason_for_visit', 'notes',
            'patient_plan_id' # <-- Añadir campo
        ]

    def validate(self, data):
        # ... (Toda tu lógica de validación de horario, disponibilidad, etc. no cambia)
        # ... (Asegúrate de copiarla aquí)

        psychologist = data.get('psychologist')
        appointment_date = data.get('appointment_date')
        start_time = data.get('start_time')
        patient = self.context['request'].user
        patient_plan_id = data.get('patient_plan_id')

        if not psychologist or not appointment_date or not start_time:
             raise serializers.ValidationError("Psicólogo, fecha y hora de inicio son requeridos.")

        # --- (Validación de horario...) ---
        # ... (Copia tu lógica de validación de horario aquí) ...


        # --- 👇 NUEVA LÓGICA DE VALIDACIÓN DE PLAN (CU-44) 👇 ---
        if patient_plan_id:
            try:
                # 1. El paciente está intentando usar un plan
                plan = PatientPlan.objects.get(
                    id=patient_plan_id,
                    patient=patient,
                    is_active=True
                )

                # 2. Validar que el plan sea con este psicólogo
                if plan.plan.psychologist != psychologist:
                    raise serializers.ValidationError("Este plan no es válido para el psicólogo seleccionado.")

                # 3. Validar que queden sesiones
                if plan.sessions_remaining <= 0:
                    raise serializers.ValidationError("No te quedan sesiones en este plan.")

                # 4. ¡Todo OK! Marcamos la cita como pagada
                data['is_paid'] = True
                data['status'] = 'confirmed'
                data['consultation_fee'] = 0 # ¡Es gratis!

            except PatientPlan.DoesNotExist:
                raise serializers.ValidationError("El plan de cuidado seleccionado no es válido.")
        else:
            # El paciente NO está usando un plan
            data['is_paid'] = False
            data['status'] = 'pending' # Requiere pago
            data['consultation_fee'] = psychologist.professional_profile.consultation_fee

        return data

    def create(self, validated_data):
        patient_plan_id = validated_data.pop('patient_plan_id', None)
        validated_data['patient'] = self.context['request'].user

        # (Calculamos end_time como antes)
        if 'end_time' not in validated_data and hasattr(validated_data['psychologist'], 'professional_profile'):
            psychologist = validated_data['psychologist']
            duration = psychologist.professional_profile.session_duration
            start_datetime = datetime.combine(
                validated_data['appointment_date'],
                validated_data['start_time']
            )
            end_datetime = start_datetime + timedelta(minutes=duration)
            validated_data['end_time'] = end_datetime.time()
            # 1. Asigna el ID del plan a la cita antes de crearla
        if patient_plan_id:
            validated_data['patient_plan_id'] = patient_plan_id

        # 2. Crea la Cita (¡YA NO DESCUENTA NADA!)
        appointment = super().create(validated_data)

        # 3. (Opcional) Añadir nota, pero YA NO restar sesiones
        if patient_plan_id:
            # Aseguramos que 'notes' no sea None
            appointment.notes = (appointment.notes or "") + f"\n[Agendada con Plan ID: {patient_plan_id}]"
            appointment.save(update_fields=['notes'])
        # --- 👆 FIN DE LA MODIFICACIÓN 👆 ---

        return appointment


class AvailablePsychologistSerializer(serializers.ModelSerializer):
    """Serializer para mostrar psicólogos disponibles con sus slots de tiempo"""
    professional_profile = ProfessionalProfileSerializer(read_only=True)
    available_slots = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name',
            'professional_profile', 'available_slots'
        ]
    
    def get_available_slots(self, obj):
        # Obtener los parámetros de búsqueda del contexto
        request = self.context.get('request')
        if not request:
            return []
        
        date_str = request.query_params.get('date')
        if not date_str:
            return []
        
        try:
            search_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return []
        
        # Obtener disponibilidad del día
        weekday = search_date.weekday()
        availabilities = obj.availabilities.filter(
            weekday=weekday,
            is_active=True
        )
        
        slots = []
        for availability in availabilities:
            # Verificar si la fecha está bloqueada
            if str(search_date) in availability.blocked_dates:
                continue
            
            # Generar slots de tiempo disponibles
            current_time = datetime.combine(search_date, availability.start_time)
            end_time = datetime.combine(search_date, availability.end_time)
            
            # Duración de sesión
            duration = 60  # Default
            if hasattr(obj, 'professional_profile'):
                duration = obj.professional_profile.session_duration
            
            while current_time + timedelta(minutes=duration) <= end_time:
                slot_start = current_time.time()
                slot_end = (current_time + timedelta(minutes=duration)).time()
                
                # Verificar si el slot está ocupado
                is_booked = Appointment.objects.filter(
                    psychologist=obj,
                    appointment_date=search_date,
                    start_time__lt=slot_end,
                    end_time__gt=slot_start,
                    status__in=['pending', 'confirmed']
                ).exists()
                
                if not is_booked:
                    slots.append({
                        'start_time': slot_start.strftime('%H:%M'),
                        'end_time': slot_end.strftime('%H:%M'),
                        'is_available': True
                    })
                
                current_time += timedelta(minutes=duration)
        
        return slots


class AppointmentUpdateSerializer(serializers.ModelSerializer):
    """Serializer para actualizar citas (cambiar estado, agregar notas, reprogramar)"""
    
    class Meta:
        model = Appointment
        fields = [
            'status', 
            'notes', 
            'meeting_link',
            'appointment_date',  # <- AÑADIDO para reprogramación
            'start_time'         # <- AÑADIDO para reprogramación
        ]
    
    def validate_status(self, value):
        # Solo permitir ciertas transiciones de estado
        if self.instance:
            current_status = self.instance.status
            valid_transitions = {
                'pending': ['confirmed', 'cancelled'],
                'confirmed': ['completed', 'cancelled', 'no_show'],
                'cancelled': [],  # No se puede cambiar desde cancelado
                'completed': [],  # No se puede cambiar desde completado
                'no_show': []     # No se puede cambiar desde no_show
            }
            
            if value not in valid_transitions.get(current_status, []):
                raise serializers.ValidationError(
                    f"No se puede cambiar de {current_status} a {value}"
                )
        
        return value

class ReferralCreateSerializer(serializers.Serializer):
    """
    Serializer simple para crear una derivación.
    Valida el ID del psicólogo y el motivo.
    """
    referred_psychologist_id = serializers.IntegerField(required=True)
    reason = serializers.CharField(required=True, max_length=1000)

    def validate_referred_psychologist_id(self, value):
        # Validamos que el ID corresponda a un psicólogo activo
        try:
            user = User.objects.get(id=value, user_type='professional', is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError("El psicólogo seleccionado no es válido o está inactivo.")
        return value