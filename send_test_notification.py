#!/usr/bin/env python
"""
Script para enviar notificación de prueba con token conocido
"""
import os
import sys
import django

# Configurar Django
sys.path.insert(0, os.path.dirname(__file__))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.notifications.fcm_service import send_fcm_notification

print("=" * 60)
print("🔔 ENVIANDO NOTIFICACIÓN DE PRUEBA")
print("=" * 60)
print()

# Token del dispositivo (del log de Flutter)
# Nota: Este token lo obtuvimos de los logs de la app
fcm_token = input("Pega el token FCM completo (de los logs de Flutter): ").strip()

if not fcm_token:
    print("❌ Token vacío")
    sys.exit(1)

print()
print(f"📤 Enviando notificación a token: {fcm_token[:50]}...")
print()

# Enviar notificación
result = send_fcm_notification(
    fcm_token=fcm_token,
    title="🎉 ¡Notificación de Prueba!",
    body="Si ves esto, las notificaciones FCM están funcionando perfectamente en tu dispositivo",
    data={
        "type": "test",
        "source": "backend_django",
        "timestamp": "2025-11-25 00:47:00"
    }
)

print()
print("📊 RESULTADO:")
print("=" * 60)

if result['success']:
    print("✅ NOTIFICACIÓN ENVIADA EXITOSAMENTE")
    print(f"   Message ID: {result['message_id']}")
    print()
    print("🎯 VERIFICA TU DISPOSITIVO:")
    print("   Deberías ver una notificación ahora mismo")
    print()
    print("✨ Si ves la notificación, ¡todo funciona perfectamente!")
else:
    print("❌ ERROR AL ENVIAR")
    print(f"   Error: {result['error']}")

print("=" * 60)
