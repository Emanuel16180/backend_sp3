# apps/clinic_admin/serializers.py
from rest_framework import serializers
from apps.tenants.models import Clinic

class BackupConfigSerializer(serializers.ModelSerializer):
    """
    Serializer para que el Admin de la clínica
    pueda leer y actualizar la configuración de backups.
    """
    
    # Obtenemos las opciones del modelo para validarlas
    backup_schedule = serializers.ChoiceField(
        choices=Clinic.SCHEDULE_CHOICES
    )
    
    class Meta:
        model = Clinic
        fields = [
            'backup_schedule',  # El campo que el admin puede CAMBIAR
            'last_backup_at'    # El campo que el admin puede LEER
        ]
        read_only_fields = ['last_backup_at']