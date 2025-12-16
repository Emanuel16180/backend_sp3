#!/usr/bin/env python
"""
Script para enviar notificación al dispositivo del usuario
Token extraído de los logs de Flutter
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.notifications.fcm_service import send_fcm_notification
from django_tenants.utils import schema_context
from apps.notifications.models import PushSubscription

print("=" * 60)
print("🔔 ENVIANDO NOTIFICACIÓN DE PRUEBA")
print("=" * 60)
print()

# Buscar el token más reciente en la base de datos
with schema_context('bienestar'):
    # Obtener la última suscripción FCM registrada
    subscription = PushSubscription.objects.filter(
        platform__in=['android', 'ios'],
        fcm_token__isnull=False,
        is_active=True
    ).order_by('-created_at').first()
    
    if not subscription:
        print("❌ No se encontró ninguna suscripción FCM activa")
        print("   Asegúrate de que la app Flutter esté corriendo y registró el token")
        sys.exit(1)
    
    fcm_token = subscription.fcm_token
    user_email = subscription.user.email
    
    print(f"📱 Token encontrado en DB para: {user_email}")
    print(f"   Token (primeros 50 chars): {fcm_token[:50]}...")
    print(f"   Platform: {subscription.platform}")
    print(f"   Registrado: {subscription.created_at}")
    print()

print("📤 Enviando notificación de prueba...")
print()

# Enviar notificación
result = send_fcm_notification(
    fcm_token=fcm_token,
    title="🎉 ¡Prueba Exitosa!",
    body="Si ves esta notificación, el sistema FCM está funcionando perfectamente",
    data={
        "type": "test",
        "source": "backend_django",
        "message": "Notificación enviada desde Python script",
        "user": user_email
    }
)

print()
print("📊 RESULTADO:")
print("=" * 60)

if result['success']:
    print("✅ ¡NOTIFICACIÓN ENVIADA EXITOSAMENTE!")
    print(f"   Message ID: {result['message_id']}")
    print()
    print("🎯 VERIFICA TU DISPOSITIVO ANDROID:")
    print("   • Si la app está abierta: Verás una notificación local")
    print("   • Si la app está en background: Notificación del sistema")
    print("   • Si la app está cerrada: Notificación del sistema")
    print()
    print("✨ ¡El sistema de notificaciones FCM funciona!")
else:
    print("❌ ERROR AL ENVIAR NOTIFICACIÓN")
    print(f"   Error: {result['error']}")
    print()
    print("💡 Posibles causas:")
    if result['error'] == 'Token no registrado o expirado':
        print("   • El token FCM ha expirado o fue invalidado")
        print("   • Solución: Reinicia la app Flutter para obtener un token fresco")
    elif result['error'] == 'Firebase no inicializado':
        print("   • Falta el archivo de credenciales Firebase")
        print("   • Verifica: psicoadmin-94485-firebase-adminsdk-fbsvc-f398acf5a8.json")
    else:
        print(f"   • {result['error']}")

print("=" * 60)
print()
