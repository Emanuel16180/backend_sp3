# apps/clinic_admin/serializers.py
from rest_framework import serializers
from apps.tenants.models import Clinic

class BackupConfigSerializer(serializers.ModelSerializer):
    """
    Serializer para leer y actualizar la configuración de backups.
    """
    
    backup_schedule = serializers.ChoiceField(choices=Clinic.SCHEDULE_CHOICES)
    
    # Campo para la fecha específica
    next_scheduled_backup = serializers.DateTimeField(
        required=False, 
        allow_null=True,
        format="%Y-%m-%d %H:%M:%S" # Formato legible
    )
    
    class Meta:
        model = Clinic
        fields = [
            'backup_schedule',
            'next_scheduled_backup', # <--- Agregamos el campo aquí
            'last_backup_at'
        ]
        read_only_fields = ['last_backup_at']
        
    def validate(self, data):
        """Validación extra"""
        schedule = data.get('backup_schedule')
        next_date = data.get('next_scheduled_backup')
        
        if schedule == 'scheduled' and not next_date:
            raise serializers.ValidationError("Si eliges 'Programado por Fecha', debes especificar la fecha y hora.")
            
        return data