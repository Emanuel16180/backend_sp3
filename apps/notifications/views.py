from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.conf import settings
from django.utils import timezone
from pywebpush import webpush, WebPushException
import json
import logging

from .models import PushSubscription, PushNotification
from .serializers import (
    PushSubscriptionSerializer,
    SendPushNotificationSerializer,
    PushNotificationSerializer
)

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def subscribe_push(request):
    """
    Suscribir al usuario a notificaciones push.
    
    POST /api/notifications/subscribe/
    Body: {
        "endpoint": "https://fcm.googleapis.com/fcm/send/...",
        "keys": {
            "p256dh": "...",
            "auth": "..."
        }
    }
    """
    serializer = PushSubscriptionSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if serializer.is_valid():
        subscription = serializer.save()
        
        logger.info(f"✅ Usuario {request.user.email} suscrito a push notifications")
        
        return Response({
            'success': True,
            'message': 'Suscripción exitosa a notificaciones push'
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def unsubscribe_push(request):
    """
    Desuscribir al usuario de notificaciones push.
    
    POST /api/notifications/unsubscribe/
    Body: {
        "endpoint": "https://fcm.googleapis.com/fcm/send/..."
    }
    """
    endpoint = request.data.get('endpoint')
    
    if not endpoint:
        return Response(
            {'error': 'endpoint es requerido'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    deleted_count = PushSubscription.objects.filter(
        user=request.user,
        endpoint=endpoint
    ).delete()[0]
    
    if deleted_count > 0:
        logger.info(f"✅ Usuario {request.user.email} desuscrito de push notifications")
        return Response({
            'success': True,
            'message': 'Desuscripción exitosa'
        })
    
    return Response({
        'success': False,
        'message': 'Suscripción no encontrada'
    }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_push_notification(request):
    """
    Enviar notificación push a uno o varios usuarios.
    Requiere permisos de admin o staff.
    
    POST /api/notifications/send/
    Body: {
        "user_id": 123,  // o "user_ids": [123, 456]
        "title": "Nueva cita",
        "body": "Tienes una cita el 25/11 a las 10:00",
        "url": "/appointments/123",  // opcional
        "icon": "/icons/icon-192x192.png"  // opcional
    }
    """
    # Verificar permisos (staff, admin, o professional)
    if not (request.user.is_staff or request.user.user_type in ['admin', 'professional']):
        return Response(
            {'error': 'No tienes permisos para enviar notificaciones'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = SendPushNotificationSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    
    # Determinar usuarios destinatarios
    user_ids = []
    if data.get('user_id'):
        user_ids = [data['user_id']]
    elif data.get('user_ids'):
        user_ids = data['user_ids']
    
    # Preparar payload de la notificación
    payload = {
        'title': data['title'],
        'body': data['body'],
        'url': data.get('url', '/'),
        'icon': data.get('icon', '/icons/icon-192x192.png'),
    }
    
    results = {
        'total': len(user_ids),
        'sent': 0,
        'failed': 0,
        'errors': []
    }
    
    # Enviar a cada usuario
    for user_id in user_ids:
        result = _send_push_to_user(user_id, payload)
        if result['success']:
            results['sent'] += result['count']
        else:
            results['failed'] += 1
            results['errors'].append({
                'user_id': user_id,
                'error': result['error']
            })
    
    return Response(results, status=status.HTTP_200_OK)


def _send_push_to_user(user_id, payload):
    """
    Función interna para enviar notificación push a un usuario específico.
    Envía a todos los dispositivos suscritos del usuario.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {
            'success': False,
            'error': f'Usuario {user_id} no encontrado',
            'count': 0
        }
    
    # Obtener todas las suscripciones activas del usuario
    subscriptions = PushSubscription.objects.filter(
        user=user,
        is_active=True
    )
    
    if not subscriptions.exists():
        return {
            'success': False,
            'error': f'Usuario {user.email} no tiene suscripciones activas',
            'count': 0
        }
    
    sent_count = 0
    vapid_claims = {
        "sub": f"mailto:{settings.VAPID_CLAIM_EMAIL}"
    }
    
    # Crear registro de notificación
    notification = PushNotification.objects.create(
        user=user,
        title=payload['title'],
        body=payload['body'],
        url=payload.get('url'),
        icon=payload.get('icon'),
        status='pending'
    )
    
    # Enviar a cada dispositivo
    for subscription in subscriptions:
        try:
            webpush(
                subscription_info=subscription.to_dict(),
                data=json.dumps(payload),
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims=vapid_claims
            )
            
            subscription.last_used = timezone.now()
            subscription.save()
            sent_count += 1
            
            logger.info(f"✅ Push enviado a {user.email}")
            
        except WebPushException as e:
            logger.error(f"❌ Error enviando push a {user.email}: {str(e)}")
            
            # Si el endpoint expiró (410), desactivar suscripción
            if e.response and e.response.status_code == 410:
                subscription.is_active = False
                subscription.save()
                logger.info(f"🗑️ Suscripción desactivada (endpoint expirado)")
    
    # Actualizar estado de la notificación
    if sent_count > 0:
        notification.status = 'sent'
        notification.sent_at = timezone.now()
    else:
        notification.status = 'failed'
        notification.error_message = 'No se pudo enviar a ningún dispositivo'
    
    notification.save()
    
    return {
        'success': sent_count > 0,
        'count': sent_count,
        'error': None if sent_count > 0 else 'No se envió a ningún dispositivo'
    }


@api_view(['GET'])
@permission_classes([AllowAny])
def get_vapid_public_key(request):
    """
    Obtener la clave pública VAPID para suscripciones.
    Endpoint público - no requiere autenticación.
    
    GET /api/notifications/vapid-public-key/
    """
    return Response({
        'public_key': settings.VAPID_PUBLIC_KEY
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notification_history(request):
    """
    Obtener historial de notificaciones del usuario.
    
    GET /api/notifications/history/
    """
    notifications = PushNotification.objects.filter(
        user=request.user
    ).order_by('-created_at')[:50]
    
    serializer = PushNotificationSerializer(notifications, many=True)
    
    return Response({
        'count': notifications.count(),
        'results': serializer.data
    })
