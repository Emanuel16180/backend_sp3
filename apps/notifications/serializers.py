from rest_framework import serializers
from .models import PushSubscription, PushNotification


class PushSubscriptionSerializer(serializers.Serializer):
    """
    Serializer para recibir suscripciones del frontend.
    """
    endpoint = serializers.URLField(max_length=500)
    keys = serializers.DictField(
        child=serializers.CharField()
    )
    
    def validate_keys(self, value):
        """Validar que keys contenga p256dh y auth"""
        if 'p256dh' not in value or 'auth' not in value:
            raise serializers.ValidationError(
                "keys debe contener 'p256dh' y 'auth'"
            )
        return value
    
    def create(self, validated_data):
        """Crear o actualizar suscripción"""
        user = self.context['request'].user
        endpoint = validated_data['endpoint']
        keys = validated_data['keys']
        
        subscription, created = PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults={
                'user': user,
                'p256dh': keys['p256dh'],
                'auth': keys['auth'],
                'user_agent': self.context['request'].META.get('HTTP_USER_AGENT', ''),
                'is_active': True,
            }
        )
        
        return subscription


class SendPushNotificationSerializer(serializers.Serializer):
    """
    Serializer para enviar notificaciones push.
    """
    user_id = serializers.IntegerField(required=False)
    user_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False
    )
    title = serializers.CharField(max_length=255)
    body = serializers.CharField()
    url = serializers.CharField(max_length=500, required=False, allow_blank=True)
    icon = serializers.URLField(required=False, allow_blank=True)
    
    def validate(self, data):
        """Validar que se proporcione user_id o user_ids"""
        if not data.get('user_id') and not data.get('user_ids'):
            raise serializers.ValidationError(
                "Debe proporcionar 'user_id' o 'user_ids'"
            )
        return data


class PushNotificationSerializer(serializers.ModelSerializer):
    """
    Serializer para ver historial de notificaciones.
    """
    class Meta:
        model = PushNotification
        fields = [
            'id', 'title', 'body', 'url', 'icon',
            'status', 'error_message', 'created_at', 'sent_at'
        ]
        read_only_fields = fields
