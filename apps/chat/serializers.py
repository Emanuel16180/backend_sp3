# apps/chat/serializers.py
from rest_framework import serializers
from .models import ChatMessage

class ChatMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.username', read_only=True)
    
    class Meta:
        model = ChatMessage
        fields = ['id', 'appointment_id', 'sender', 'sender_name', 'message', 'timestamp']
        read_only_fields = ['sender', 'timestamp']