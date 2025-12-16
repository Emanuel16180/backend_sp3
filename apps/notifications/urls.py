from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    # Suscripción Web Push
    path('subscribe/', views.subscribe_push, name='subscribe_push'),
    path('unsubscribe/', views.unsubscribe_push, name='unsubscribe_push'),
    path('vapid-public-key/', views.get_vapid_public_key, name='vapid_public_key'),
    
    # Envío Web Push
    path('send/', views.send_push_notification, name='send_push'),
    
    # Notificaciones Móviles FCM
    path('mobile/register-token/', views.register_fcm_token, name='register_fcm_token'),
    path('mobile/unregister-token/', views.unregister_fcm_token, name='unregister_fcm_token'),
    path('mobile/send/', views.send_fcm_push, name='send_fcm_push'),
    
    # Historial
    path('history/', views.notification_history, name='notification_history'),
]
