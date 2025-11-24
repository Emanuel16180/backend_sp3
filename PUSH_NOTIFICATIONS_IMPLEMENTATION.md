# 🔔 Sistema de Notificaciones Push - Implementación Backend

## ✅ Componentes Implementados

### 1. **Aplicación Django** (`apps/notifications/`)
- ✅ `models.py` - Modelos de datos:
  - `PushSubscription`: Almacena suscripciones de navegadores/dispositivos
  - `PushNotification`: Registro de notificaciones enviadas
  
- ✅ `serializers.py` - Validación de datos:
  - `PushSubscriptionSerializer`: Validación de endpoint y llaves
  - `SendPushNotificationSerializer`: Validación de envío
  - `PushNotificationSerializer`: Lectura de historial
  
- ✅ `views.py` - Endpoints API:
  - `POST /api/notifications/subscribe/` - Suscribir dispositivo
  - `POST /api/notifications/unsubscribe/` - Desuscribir dispositivo
  - `POST /api/notifications/send/` - Enviar notificación (solo admins)
  - `GET /api/notifications/vapid-public-key/` - Obtener clave pública
  - `GET /api/notifications/history/` - Ver historial de notificaciones
  
- ✅ `admin.py` - Panel de administración
- ✅ `urls.py` - Configuración de rutas

### 2. **Configuración de Django**
- ✅ Añadida `apps.notifications` a `INSTALLED_APPS` en `TENANT_APPS`
- ✅ Configuración de VAPID en `settings.py`:
  - `VAPID_PUBLIC_KEY`
  - `VAPID_PRIVATE_KEY`
  - `VAPID_CLAIM_EMAIL`
- ✅ URLs incluidas en `config/urls.py`

### 3. **Base de Datos**
- ✅ Migraciones creadas: `0001_initial.py`
- ✅ Migraciones aplicadas en todos los schemas:
  - `public`
  - `bienestar`
  - `mindcare`
- ✅ Tablas creadas:
  - `push_subscriptions`
  - `push_notifications`

### 4. **Dependencias Instaladas**
- ✅ `pywebpush==2.1.2` - Cliente para enviar notificaciones web push
- ✅ `py-vapid==1.9.2` - Generación y manejo de llaves VAPID

### 5. **Llaves VAPID Generadas**
- ✅ Script de generación: `generate_vapid_keys.py`
- ✅ Llaves generadas (EC P-256):
  - Clave pública: `BNVdhBTDqH9WQRtYuLqy1VjA7QSEZPwlM0vgxmVn4K3a6to8unUoie_ZaqA8TzXAg49ExZ8PXqccm63T0tmq_j0`
  - Clave privada: (almacenar en variables de entorno)

### 6. **Scripts de Prueba**
- ✅ `test_push_notifications.ps1` - Script PowerShell para probar endpoints

## 📋 Próximos Pasos

### 1. **Configurar Variables de Entorno en Render**
Añade estas variables en el dashboard de Render:

```bash
VAPID_PUBLIC_KEY=BNVdhBTDqH9WQRtYuLqy1VjA7QSEZPwlM0vgxmVn4K3a6to8unUoie_ZaqA8TzXAg49ExZ8PXqccm63T0tmq_j0

VAPID_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgJ9ZKB26RDV217Xip
UofytQs9hzxHJHbUDEoPafphZz6hRANCAATVXYQUw6h/VkEbWLi6stVYwO0EhGT8
JTNL4MZlZ+Ct2uraPLp1KInv2WqgPE81wIOPRMWfD16nHJut09LZqv49
-----END PRIVATE KEY-----

VAPID_CLAIM_EMAIL=admin@psicoadmin.xyz
```

### 2. **Desplegar Backend**
```bash
git add .
git commit -m "feat: implementar sistema de notificaciones push con VAPID"
git push origin main
```

Render automáticamente detectará los cambios y redesplegará.

### 3. **Verificar Despliegue**
- Revisar logs de Render para confirmar migraciones exitosas
- Probar endpoint público: `GET https://api.psicoadmin.xyz/api/notifications/vapid-public-key/`

### 4. **Implementar Frontend (PWA)**
Seguir la guía en `PUSH_NOTIFICATIONS_GUIDE.md`:
- Implementar Service Worker con manejador de eventos `push`
- Crear componente de suscripción en React
- Solicitar permiso de notificaciones al usuario
- Registrar suscripción con el backend

## 🔧 Características del Sistema

### Seguridad
- ✅ Autenticación requerida para suscribirse/desuscribirse
- ✅ Solo administradores pueden enviar notificaciones
- ✅ Llaves VAPID únicas para verificación de origen
- ✅ Suscripciones vinculadas a usuarios específicos

### Gestión de Suscripciones
- ✅ Una suscripción por endpoint (navegador/dispositivo)
- ✅ Auto-desactivación de endpoints expirados (HTTP 410)
- ✅ Múltiples dispositivos por usuario soportados
- ✅ Registro de user-agent para identificación

### Notificaciones
- ✅ Título y cuerpo personalizables
- ✅ URL opcional para navegación al hacer clic
- ✅ Icono personalizable
- ✅ Historial completo con timestamps
- ✅ Estados: pending, sent, failed
- ✅ Registro de errores para debugging

### Escalabilidad
- ✅ Envío batch a múltiples usuarios
- ✅ Manejo de múltiples dispositivos por usuario
- ✅ Sistema multi-tenant (cada clínica independiente)

## 🧪 Probar el Sistema

### Opción 1: Script PowerShell
```powershell
.\test_push_notifications.ps1
```

### Opción 2: Curl/PowerShell Manual

**Obtener clave pública:**
```powershell
$response = Invoke-RestMethod -Uri "https://api.psicoadmin.xyz/api/notifications/vapid-public-key/" `
    -Headers @{"X-Tenant-Schema" = "bienestar"}
$response.public_key
```

**Suscribir dispositivo:**
```powershell
$token = "tu_token_aqui"
$body = @{
    endpoint = "https://fcm.googleapis.com/fcm/send/endpoint-unico"
    keys = @{
        p256dh = "clave_p256dh_del_navegador"
        auth = "clave_auth_del_navegador"
    }
} | ConvertTo-Json

Invoke-RestMethod -Uri "https://api.psicoadmin.xyz/api/notifications/subscribe/" `
    -Method POST `
    -Headers @{
        "Authorization" = "Token $token"
        "X-Tenant-Schema" = "bienestar"
        "Content-Type" = "application/json"
    } `
    -Body $body
```

## 📚 Documentación Completa

Ver `PUSH_NOTIFICATIONS_GUIDE.md` para:
- Implementación completa del frontend
- Ejemplos de código Service Worker
- Componentes React
- Manejo de permisos
- Testing y debugging

## ⚠️ Notas Importantes

1. **Llaves VAPID**: Son secretas y únicas. No regenerar sin migrar suscripciones existentes.
2. **HTTPS Requerido**: Las notificaciones push solo funcionan en HTTPS (excepto localhost).
3. **Permisos del Navegador**: El usuario debe autorizar notificaciones explícitamente.
4. **Service Worker**: Requerido en el frontend para recibir notificaciones.
5. **Multi-Tenant**: Cada clínica tiene sus propias suscripciones y notificaciones separadas.

## 🐛 Troubleshooting

**Error: "No module named 'vapid'"**
- Solución: Usar `py_vapid` en lugar de `vapid`

**Error: "curve must be an EllipticCurve instance"**
- Solución: Usar `cryptography` directamente (ver `generate_vapid_keys.py`)

**Error: "VAPID_PUBLIC_KEY not configured"**
- Solución: Verificar variables de entorno en Render

**Notificaciones no llegan:**
- Verificar que Service Worker esté registrado
- Verificar permisos de notificaciones en el navegador
- Revisar consola del navegador para errores
- Verificar que el endpoint no esté expirado (revisar logs del backend)
