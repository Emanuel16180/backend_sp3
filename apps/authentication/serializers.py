# apps/authentication/serializers.py

from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

User = get_user_model()

class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer para registro de paciente en el centro de salud mental - CU-01
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
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Este nombre de usuario ya existe")
        return value
    
    def validate_date_of_birth(self, value):
        from datetime import date
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
        validated_data['user_type'] = 'patient'  # Solo pacientes se registran por la app
        
        user = User.objects.create_user(**validated_data)
        user.set_password(password)
        user.save()
        return user


# apps/authentication/serializers.py

# ... (importaciones) ...

class UserLoginSerializer(serializers.Serializer):
    """
    Serializer para login de usuario - CU-02
    """
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if not email or not password:
            raise serializers.ValidationError('Email y contraseña son requeridos')

        # --- LÍNEAS CLAVE CORREGIDAS ---
        # El backend TenantAwareAuthBackend DEBE encargarse de buscar el usuario
        # en el modelo (PublicUser o CustomUser) correcto.
        # Necesitamos obtener el request del contexto del serializer
        request = self.context.get('request')
        user = authenticate(request=request, username=email, password=password)

        # Si 'authenticate' falla, es por credenciales inválidas o usuario inactivo.
        if not user or not user.is_active:
            raise serializers.ValidationError("Credenciales inválidas o usuario inactivo.")
        # --- FIN LÍNEAS CLAVE CORREGIDAS ---

        attrs['user'] = user
        return attrs

# ... (resto del archivo)

class PasswordResetRequestSerializer(serializers.Serializer):
    """
    Serializer para solicitar reset de contraseña - CU-04
    """
    email = serializers.EmailField()
    
    def validate_email(self, value):
        if not User.objects.filter(email=value).exists():
            raise serializers.ValidationError("No existe un usuario con este email")
        return value


class PasswordResetConfirmSerializer(serializers.Serializer):
    """
    Serializer para confirmar reset de contraseña - CU-04
    """
    # --- 1. AÑADE ESTA LÍNEA ---
    uid = serializers.CharField(write_only=True) # <-- Acepta el uid que envía el frontend

    token = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    new_password_confirm = serializers.CharField()
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        return attrs
        
class ChangePasswordSerializer(serializers.Serializer):
    """
    Serializer para cambiar contraseña - CU-05
    """
    current_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    new_password_confirm = serializers.CharField()
    
    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Contraseña actual incorrecta")
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        return attrs