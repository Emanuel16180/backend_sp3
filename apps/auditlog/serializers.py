# apps/auditlog/serializers.py
from rest_framework import serializers
from .models import LogEntry

class LogEntrySerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source='user.email', read_only=True)
    user_name = serializers.SerializerMethodField()
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    
    class Meta:
        model = LogEntry
        fields = [
            'id', 
            'timestamp', 
            'user', 
            'user_email', 
            'user_name',
            'ip_address', 
            'level', 
            'level_display',
            'action', 
            'details'
        ]
        
    def get_user_name(self, obj):
        if obj.user:
            return f"{obj.user.first_name} {obj.user.last_name}".strip()
        return "Sistema"