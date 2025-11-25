# apps/notifications/fcm_service.py
import firebase_admin
from firebase_admin import credentials, messaging
from django.conf import settings
import logging
import os
import json

logger = logging.getLogger(__name__)

# Inicializar Firebase Admin SDK
def initialize_firebase():
    """
    Inicializa Firebase Admin SDK con credenciales desde variable de entorno o archivo.
    Solo se ejecuta una vez.
    """
    if not firebase_admin._apps:
        try:
            # Intentar primero desde variable de entorno (para Render/producción)
            firebase_creds_json = os.environ.get('FIREBASE_CREDENTIALS')
            
            if firebase_creds_json:
                # Cargar credenciales desde JSON en variable de entorno
                cred_dict = json.loads(firebase_creds_json)
                cred = credentials.Certificate(cred_dict)
                firebase_admin.initialize_app(cred)
                logger.info("✅ Firebase Admin SDK inicializado desde variable de entorno")
                return True
            
            # Si no hay variable de entorno, buscar archivo (para desarrollo local)
            cred_path = os.path.join(
                settings.BASE_DIR,
                'psicoadmin-94485-firebase-adminsdk-fbsvc-f398acf5a8.json'
            )
            
            if os.path.exists(cred_path):
                cred = credentials.Certificate(cred_path)
                firebase_admin.initialize_app(cred)
                logger.info("✅ Firebase Admin SDK inicializado desde archivo")
                return True
            
            logger.error("❌ No se encontraron credenciales de Firebase (ni variable de entorno ni archivo)")
            return False
            
        except json.JSONDecodeError as e:
            logger.error(f"❌ Error decodificando JSON de FIREBASE_CREDENTIALS: {str(e)}")
            return False
            
        except Exception as e:
            logger.error(f"❌ Error inicializando Firebase: {str(e)}")
            return False
    
    return True


def send_fcm_notification(fcm_token, title, body, data=None):
    """
    Envía una notificación FCM a un token específico.
    
    Args:
        fcm_token (str): Token FCM del dispositivo
        title (str): Título de la notificación
        body (str): Cuerpo del mensaje
        data (dict): Datos adicionales opcionales
    
    Returns:
        dict: {'success': bool, 'message_id': str or None, 'error': str or None}
    """
    if not initialize_firebase():
        return {
            'success': False,
            'message_id': None,
            'error': 'Firebase no inicializado'
        }
    
    try:
        # Crear mensaje FCM
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            token=fcm_token,
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    sound='default',
                    channel_id='default',
                ),
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound='default',
                        badge=1,
                    ),
                ),
            ),
        )
        
        # Enviar mensaje
        response = messaging.send(message)
        
        logger.info(f"✅ Notificación FCM enviada exitosamente: {response}")
        
        return {
            'success': True,
            'message_id': response,
            'error': None
        }
        
    except messaging.UnregisteredError:
        logger.warning(f"⚠️ Token FCM no registrado o expirado: {fcm_token[:20]}...")
        return {
            'success': False,
            'message_id': None,
            'error': 'Token no registrado o expirado'
        }
        
    except messaging.SenderIdMismatchError:
        logger.error(f"❌ Sender ID no coincide para token: {fcm_token[:20]}...")
        return {
            'success': False,
            'message_id': None,
            'error': 'Sender ID no coincide'
        }
        
    except Exception as e:
        logger.error(f"❌ Error enviando notificación FCM: {str(e)}")
        return {
            'success': False,
            'message_id': None,
            'error': str(e)
        }


def send_fcm_to_multiple(fcm_tokens, title, body, data=None):
    """
    Envía notificación FCM a múltiples tokens (multicast).
    
    Args:
        fcm_tokens (list): Lista de tokens FCM
        title (str): Título de la notificación
        body (str): Cuerpo del mensaje
        data (dict): Datos adicionales opcionales
    
    Returns:
        dict: {'success_count': int, 'failure_count': int, 'responses': list}
    """
    if not initialize_firebase():
        return {
            'success_count': 0,
            'failure_count': len(fcm_tokens),
            'responses': []
        }
    
    if not fcm_tokens:
        return {
            'success_count': 0,
            'failure_count': 0,
            'responses': []
        }
    
    try:
        # Crear mensaje multicast
        message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            tokens=fcm_tokens,
            android=messaging.AndroidConfig(
                priority='high',
                notification=messaging.AndroidNotification(
                    sound='default',
                    channel_id='default',
                ),
            ),
            apns=messaging.APNSConfig(
                payload=messaging.APNSPayload(
                    aps=messaging.Aps(
                        sound='default',
                        badge=1,
                    ),
                ),
            ),
        )
        
        # Enviar mensaje
        response = messaging.send_multicast(message)
        
        logger.info(
            f"✅ Notificaciones FCM enviadas: "
            f"{response.success_count} exitosas, {response.failure_count} fallidas"
        )
        
        return {
            'success_count': response.success_count,
            'failure_count': response.failure_count,
            'responses': [
                {
                    'success': resp.success,
                    'message_id': resp.message_id if resp.success else None,
                    'error': str(resp.exception) if not resp.success else None
                }
                for resp in response.responses
            ]
        }
        
    except Exception as e:
        logger.error(f"❌ Error enviando notificaciones FCM multicast: {str(e)}")
        return {
            'success_count': 0,
            'failure_count': len(fcm_tokens),
            'responses': []
        }
