# apps/backups/serializers.py
from rest_framework import serializers
from .models import BackupRecord

class BackupRecordSerializer(serializers.ModelSerializer):
    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    
    class Meta:
        model = BackupRecord
        fields = [
            'id',
            'file_name',
            'file_path',
            'file_size',
            'backup_type',
            'created_by_email',
            'created_at'
        ]