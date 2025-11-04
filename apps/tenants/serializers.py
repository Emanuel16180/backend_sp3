# apps/tenants/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import Clinic, Domain
import re

User = get_user_model()

class DomainSerializer(serializers.ModelSerializer):
    class Meta:
        model = Domain
        fields = ['domain', 'is_primary']

class ClinicSerializer(serializers.ModelSerializer):
    domains = DomainSerializer(many=True, read_only=True)
    
    class Meta:
        model = Clinic
        fields = ['id', 'name', 'schema_name', 'created_on', 'domains']
        read_only_fields = ['created_on', 'domains']

class ClinicCreateSerializer(serializers.ModelSerializer):
    domain = serializers.CharField(write_only=True, help_text="Dominio principal para la clínica")
    
    class Meta:
        model = Clinic
        fields = ['name', 'schema_name', 'domain']
    
    def validate_schema_name(self, value):
        """Validar que el schema_name sea válido"""
        if not value.isalnum():
            raise serializers.ValidationError("El nombre del esquema debe contener solo letras y números")
        if value in ['public', 'postgres', 'information_schema']:
            raise serializers.ValidationError("El nombre del esquema no puede ser una palabra reservada")
        return value.lower()
    
    def validate_domain(self, value):
        """Validar que el dominio no esté en uso"""
        if Domain.objects.filter(domain=value).exists():
            raise serializers.ValidationError("Este dominio ya está en uso")
        return value
    
    def create(self, validated_data):
        domain_name = validated_data.pop('domain')
        clinic = Clinic.objects.create(**validated_data)
        
        # Crear el dominio asociado
        Domain.objects.create(
            domain=domain_name,
            tenant=clinic,
            is_primary=True
        )
        
        return clinic


# ========== SERIALIZERS PARA REGISTRO PÚBLICO ==========

class TenantRegistrationSerializer(serializers.Serializer):
    """
    Serializer para registro público de nuevos tenants (clínicas)
    """
    clinic_name = serializers.CharField(
        max_length=100,
        required=True,
        help_text="Nombre de la clínica"
    )
    subdomain = serializers.CharField(
        max_length=63,
        required=True,
        help_text="Subdominio deseado (ej: miclinica para miclinica.psicoadmin.xyz)"
    )
    admin_email = serializers.EmailField(
        required=True,
        help_text="Email del administrador de la clínica"
    )
    admin_phone = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        help_text="Teléfono de contacto (opcional)"
    )
    address = serializers.CharField(
        max_length=200,
        required=False,
        allow_blank=True,
        help_text="Dirección de la clínica (opcional)"
    )

    def validate_subdomain(self, value):
        """
        Validar que el subdominio sea válido y no esté en uso
        """
        # Convertir a minúsculas y eliminar espacios
        value = value.lower().strip()
        
        # Validar formato (solo letras, números y guiones)
        if not re.match(r'^[a-z0-9-]+$', value):
            raise serializers.ValidationError(
                "El subdominio solo puede contener letras minúsculas, números y guiones"
            )
        
        # No puede empezar o terminar con guión
        if value.startswith('-') or value.endswith('-'):
            raise serializers.ValidationError(
                "El subdominio no puede empezar ni terminar con guión"
            )
        
        # Mínimo 3 caracteres
        if len(value) < 3:
            raise serializers.ValidationError(
                "El subdominio debe tener al menos 3 caracteres"
            )
        
        # Subdominios reservados
        reserved_subdomains = [
            'www', 'api', 'admin', 'app', 'mail', 'email',
            'ftp', 'ssh', 'public', 'static', 'media', 'cdn',
            'test', 'dev', 'staging', 'prod', 'production',
            'bienestar', 'mindcare'  # Los que ya existen
        ]
        if value in reserved_subdomains:
            raise serializers.ValidationError(
                f"El subdominio '{value}' está reservado. Por favor, elige otro."
            )
        
        # Verificar que no exista ya
        domain_name = f"{value}.psicoadmin.xyz"
        if Domain.objects.filter(domain=domain_name).exists():
            raise serializers.ValidationError(
                f"El subdominio '{value}' ya está en uso. Por favor, elige otro."
            )
        
        # Verificar que el schema_name no exista
        if Clinic.objects.filter(schema_name=value).exists():
            raise serializers.ValidationError(
                f"El subdominio '{value}' ya está en uso. Por favor, elige otro."
            )
        
        return value

    def validate_admin_email(self, value):
        """
        Validar que el email no esté ya registrado en el tenant público
        """
        # Verificar en el schema público
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                "Este email ya está registrado. Por favor, usa otro email."
            )
        
        return value

    @transaction.atomic
    def create(self, validated_data):
        """
        Crear el tenant, dominio y usuario administrador
        """
        clinic_name = validated_data['clinic_name']
        subdomain = validated_data['subdomain']
        admin_email = validated_data['admin_email']
        admin_phone = validated_data.get('admin_phone', '')
        address = validated_data.get('address', '')
        
        # 1. Crear el tenant (clínica)
        tenant = Clinic.objects.create(
            schema_name=subdomain,
            name=clinic_name,
            address=address,
            phone=admin_phone,
        )
        
        # 2. Crear el dominio
        domain = Domain.objects.create(
            domain=f"{subdomain}.psicoadmin.xyz",
            tenant=tenant,
            is_primary=True
        )
        
        # 3. Crear usuario administrador en el schema del tenant
        from django_tenants.utils import schema_context
        
        with schema_context(tenant.schema_name):
            admin_user = User.objects.create_user(
                username=admin_email.split('@')[0],
                email=admin_email,
                first_name='Admin',
                last_name=clinic_name,
                phone=admin_phone,
                role='admin',
                is_staff=True,
                is_superuser=True,
            )
            # Establecer contraseña temporal
            admin_user.set_password('Admin123!')
            admin_user.save()
        
        return {
            'tenant': tenant,
            'domain': domain,
            'admin_user': admin_user,
            'subdomain': subdomain,
            'admin_email': admin_email,
            'temporary_password': 'Admin123!'
        }


class SubdomainCheckSerializer(serializers.Serializer):
    """
    Serializer para verificar disponibilidad de subdominio
    """
    subdomain = serializers.CharField(max_length=63, required=True)
    
    def validate_subdomain(self, value):
        value = value.lower().strip()
        
        if not re.match(r'^[a-z0-9-]+$', value):
            raise serializers.ValidationError(
                "El subdominio solo puede contener letras minúsculas, números y guiones"
            )
        
        return value