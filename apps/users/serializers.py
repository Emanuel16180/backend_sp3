# apps/users/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import PatientProfile
from datetime import date
from apps.clinical_history.models import InitialTriage

User = get_user_model()

# Importar serializer de perfil profesional para evitar importación circular
def get_professional_profile_serializer():
    from apps.professionals.serializers import ProfessionalProfileSerializer
    return ProfessionalProfileSerializer

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para actualizar perfil básico del usuario - CU-05
    """
    age = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'ci', 'phone', 'gender',
            'address', 'date_of_birth', 'age', 'profile_picture'
        )
        read_only_fields = ('email', 'username', 'user_type', 'ci')  # CI no se puede cambiar una vez creado
    
    def validate_date_of_birth(self, value):
        """Validar que la fecha de nacimiento sea lógica"""
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        
        if age < 5:
            raise serializers.ValidationError("La edad debe ser mayor a 5 años")
        if age > 120:
            raise serializers.ValidationError("La edad debe ser menor a 120 años")
        
        return value


class PatientProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para perfil de paciente del centro de salud mental - CU-05
    """
    pre_diagnosis = serializers.SerializerMethodField()
    recommendation = serializers.SerializerMethodField()

    class Meta:
        model = PatientProfile
        fields = (
            'emergency_contact_name', 'emergency_contact_phone', 
            'emergency_contact_relationship', 'occupation', 
            'education_level', 'initial_reason', 'how_found_us',
            'profile_completed',
            'pre_diagnosis', 'recommendation'
        )
        read_only_fields = ('profile_completed','pre_diagnosis', 'recommendation')
    
    def get_pre_diagnosis(self, obj):
        """Obtiene el pre-diagnóstico del triaje del paciente."""
        try:
            # obj es el PatientProfile, obj.user es el Paciente
            return obj.user.initial_triage.pre_diagnosis
        except InitialTriage.DoesNotExist:
            return None
        except AttributeError: # Si 'initial_triage' no existe
            return None

    def get_recommendation(self, obj):
        """Obtiene la recomendación del triaje del paciente."""
        try:
            return obj.user.initial_triage.recommendation
        except InitialTriage.DoesNotExist:
            return None
        except AttributeError:
            return None
            
    def validate(self, attrs):
        """Marcar perfil como completo si tiene los datos básicos"""
        if (attrs.get('emergency_contact_name') and 
            attrs.get('emergency_contact_phone') and 
            attrs.get('emergency_contact_relationship')):
            attrs['profile_completed'] = True
        return attrs


class UserDetailSerializer(serializers.ModelSerializer):
    """
    Serializer para mostrar información completa del usuario - CU-05
    """
    patient_profile = PatientProfileSerializer(read_only=True)
    professional_profile = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    age = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 
            'full_name', 'user_type', 'ci', 'phone', 'gender',
            'address', 'date_of_birth', 'age', 'profile_picture', 
            'is_verified', 'is_active_patient', 'date_joined', 
            'patient_profile', 'professional_profile'
        )
        read_only_fields = (
            'id', 'email', 'username', 'user_type', 'is_verified', 
            'date_joined'
        )
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_professional_profile(self, obj):
        """Retorna el perfil profesional si el usuario es un profesional"""
        if obj.user_type == 'professional' and hasattr(obj, 'professional_profile'):
            ProfessionalProfileSerializer = get_professional_profile_serializer()
            return ProfessionalProfileSerializer(obj.professional_profile).data
        return None


class PatientRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer específico para registro de pacientes - CU-01
    """
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)
    age = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = (
            'email', 'username', 'first_name', 'last_name', 'ci',
            'phone', 'gender', 'address', 'date_of_birth', 'age',
            'password', 'password_confirm'
        )
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        return attrs
    
    def validate_ci(self, value):
        if User.objects.filter(ci=value).exists():
            raise serializers.ValidationError("Esta cédula ya está registrada")
        return value
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Este email ya está registrado")
        return value
    
    def validate_date_of_birth(self, value):
        today = date.today()
        age = today.year - value.year - ((today.month, today.day) < (value.month, value.day))
        
        if age < 5:
            raise serializers.ValidationError("Debe ser mayor de 5 años")
        if age > 120:
            raise serializers.ValidationError("Edad no válida")
        
        return value
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        validated_data['user_type'] = 'patient'  # Forzar tipo paciente
        
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        
        return user


class PatientCompleteProfileSerializer(serializers.ModelSerializer):
    """
    Serializer para actualizar perfil completo de paciente - CU-05
    """
    user_data = UserProfileSerializer()
    patient_data = PatientProfileSerializer()
    
    class Meta:
        model = User
        fields = ('user_data', 'patient_data')
    
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user_data', {})
        patient_data = validated_data.pop('patient_data', {})
        
        # Actualizar datos del usuario
        if user_data:
            for attr, value in user_data.items():
                setattr(instance, attr, value)
            instance.save()
        
        # Actualizar o crear perfil de paciente
        if patient_data:
            patient_profile, created = PatientProfile.objects.get_or_create(
                user=instance,
                defaults=patient_data
            )
            if not created:
                for attr, value in patient_data.items():
                    setattr(patient_profile, attr, value)
                patient_profile.save()
        
        return instance