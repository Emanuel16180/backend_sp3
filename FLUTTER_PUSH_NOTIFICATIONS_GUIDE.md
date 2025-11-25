# Guía de Notificaciones Push con Firebase (FCM) para Flutter Mobile

Esta guía documenta la implementación de notificaciones push usando **Firebase Cloud Messaging (FCM)** en aplicaciones Flutter nativas (Android/iOS). Es diferente de las notificaciones Web Push/PWA.

## 📋 Tabla de Contenidos

1. [Diferencias con Web/PWA](#diferencias-con-webpwa)
2. [Configuración Inicial](#configuración-inicial)
3. [Endpoints del Backend](#endpoints-del-backend)
4. [Implementación Flutter](#implementación-flutter)
5. [Permisos y Configuración](#permisos-y-configuración)
6. [Manejo de Notificaciones](#manejo-de-notificaciones)
7. [Testing](#testing)

---

## 🔄 Diferencias con Web/PWA

| Característica | Web/PWA | Mobile Nativo (FCM) |
|---------------|---------|---------------------|
| **Protocolo** | Web Push (VAPID) | Firebase Cloud Messaging |
| **Token** | Endpoint + Keys | FCM Token |
| **Plataforma** | Solo navegadores | Android + iOS |
| **Configuración** | Service Worker | Firebase SDK |
| **Backend** | pywebpush | firebase-admin |

**¿Por qué FCM en mobile?**
- Notificaciones nativas del sistema
- Funciona con app cerrada
- Mejor tasa de entrega
- Soporte oficial de Google/Apple

---

## ⚙️ Configuración Inicial

### 1. Archivos Firebase (YA TIENES)

✅ **`google-services.json`** - Para Android  
✅ **`psicoadmin-94485-firebase-adminsdk-fbsvc-f398acf5a8.json`** - Para Backend (ya está en raíz)

---

### 2. Dependencias Flutter

```yaml
# pubspec.yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^1.1.0
  firebase_core: ^2.24.2
  firebase_messaging: ^14.7.10
  flutter_local_notifications: ^16.3.0
  provider: ^6.1.1
```

---

### 3. Configuración Android

#### A. Agregar `google-services.json`

1. Copia el archivo `google-services.json` que descargaste
2. Pégalo en: `android/app/google-services.json`

#### B. Configurar `build.gradle` (Proyecto)

```gradle
// android/build.gradle
buildscript {
    repositories {
        google()
        mavenCentral()
    }
    
    dependencies {
        classpath 'com.android.tools.build:gradle:7.3.0'
        classpath 'com.google.gms:google-services:4.4.0'  // ← AGREGAR
        classpath "org.jetbrains.kotlin:kotlin-gradle-plugin:$kotlin_version"
    }
}
```

#### C. Configurar `build.gradle` (App)

```gradle
// android/app/build.gradle
apply plugin: 'com.android.application'
apply plugin: 'kotlin-android'
apply plugin: 'com.google.gms.google-services'  // ← AGREGAR

android {
    defaultConfig {
        applicationId "com.psicoadmin.app"  // ← Debe coincidir con Firebase
        minSdkVersion 21  // ← Mínimo para FCM
        targetSdkVersion 33
    }
}
```

#### D. AndroidManifest.xml

```xml
<!-- android/app/src/main/AndroidManifest.xml -->
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    
    <uses-permission android:name="android.permission.INTERNET"/>
    <uses-permission android:name="android.permission.POST_NOTIFICATIONS"/>  <!-- Android 13+ -->
    
    <application
        android:label="PsicoAdmin"
        android:icon="@mipmap/ic_launcher">
        
        <activity
            android:name=".MainActivity"
            android:launchMode="singleTop">  <!-- ← IMPORTANTE para deep links -->
            <!-- ... -->
        </activity>
        
        <!-- Canal de notificaciones por defecto -->
        <meta-data
            android:name="com.google.firebase.messaging.default_notification_channel_id"
            android:value="default" />
            
    </application>
</manifest>
```

---

### 4. Configuración iOS (Opcional)

Si vas a soportar iOS, necesitas:

1. **Agregar `GoogleService-Info.plist`** a `ios/Runner/`
2. **Configurar APNs** en Apple Developer
3. **Subir APNs Key** a Firebase Console

**Por ahora nos enfocamos en Android** ✅

---

## 🔌 Endpoints del Backend

### 1. Registrar Token FCM

```http
POST /api/notifications/mobile/register-token/
X-Tenant-Schema: bienestar
Authorization: Token <user_token>
Content-Type: application/json

{
  "fcm_token": "dXm8K9hQ...",
  "platform": "android"
}
```

**Respuesta exitosa:**
```json
{
  "success": true,
  "message": "Token FCM registrado exitosamente (creada)",
  "subscription_id": 45
}
```

---

### 2. Enviar Notificación Push (Admin/Professional)

```http
POST /api/notifications/mobile/send/
X-Tenant-Schema: bienestar
Authorization: Token <admin_token>
Content-Type: application/json

{
  "user_id": 123,
  "title": "Nueva cita",
  "body": "Tienes una cita el 25/11 a las 10:00",
  "data": {
    "appointment_id": "123",
    "url": "/appointments/123"
  }
}
```

**Respuesta exitosa:**
```json
{
  "total_users": 1,
  "sent": 1,
  "failed": 0,
  "errors": []
}
```

---

### 3. Desregistrar Token (Logout)

```http
POST /api/notifications/mobile/unregister-token/
X-Tenant-Schema: bienestar
Authorization: Token <user_token>
Content-Type: application/json

{
  "fcm_token": "dXm8K9hQ..."
}
```

---

## 📱 Implementación Flutter

### 1. Inicializar Firebase

```dart
// lib/main.dart
import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'services/notification_service.dart';

// Handler para notificaciones en background
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  print('📩 Notificación en background: ${message.notification?.title}');
}

// Plugin de notificaciones locales
final FlutterLocalNotificationsPlugin flutterLocalNotificationsPlugin =
    FlutterLocalNotificationsPlugin();

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Inicializar Firebase
  await Firebase.initializeApp();
  
  // Configurar handler de background
  FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);
  
  // Configurar notificaciones locales (para Android)
  const AndroidInitializationSettings initializationSettingsAndroid =
      AndroidInitializationSettings('@mipmap/ic_launcher');
      
  const InitializationSettings initializationSettings = InitializationSettings(
    android: initializationSettingsAndroid,
  );
  
  await flutterLocalNotificationsPlugin.initialize(
    initializationSettings,
    onDidReceiveNotificationResponse: (NotificationResponse response) {
      // Manejar clic en notificación
      print('📱 Usuario clickeó notificación: ${response.payload}');
    },
  );
  
  // Crear canal de notificaciones (Android 8+)
  const AndroidNotificationChannel channel = AndroidNotificationChannel(
    'default',
    'Notificaciones Generales',
    description: 'Canal para notificaciones de la app',
    importance: Importance.high,
  );
  
  await flutterLocalNotificationsPlugin
      .resolvePlatformSpecificImplementation<AndroidFlutterLocalNotificationsPlugin>()
      ?.createNotificationChannel(channel);
  
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'PsicoAdmin',
      home: HomePage(),
    );
  }
}
```

---

### 2. Servicio de Notificaciones

```dart
// lib/services/notification_service.dart
import 'dart:convert';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:http/http.dart' as http;

class NotificationService {
  static const String baseUrl = 'https://api.psicoadmin.xyz/api/notifications';
  
  final FirebaseMessaging _firebaseMessaging = FirebaseMessaging.instance;
  final FlutterLocalNotificationsPlugin _localNotifications =
      FlutterLocalNotificationsPlugin();
  
  final String token;
  final String tenantSchema;
  
  NotificationService({
    required this.token,
    this.tenantSchema = 'bienestar',
  });
  
  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    'Authorization': 'Token $token',
    'X-Tenant-Schema': tenantSchema,
  };
  
  /// Inicializar y registrar token FCM
  Future<String?> initialize() async {
    // 1. Solicitar permisos
    NotificationSettings settings = await _firebaseMessaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );
    
    if (settings.authorizationStatus == AuthorizationStatus.denied) {
      print('❌ Permisos de notificaciones denegados');
      return null;
    }
    
    // 2. Obtener token FCM
    String? fcmToken = await _firebaseMessaging.getToken();
    
    if (fcmToken == null) {
      print('❌ No se pudo obtener token FCM');
      return null;
    }
    
    print('✅ Token FCM obtenido: ${fcmToken.substring(0, 20)}...');
    
    // 3. Registrar token en backend
    await registerToken(fcmToken);
    
    // 4. Configurar listeners
    _configureForegroundNotifications();
    _configureNotificationTapHandler();
    
    // 5. Escuchar cambios de token
    _firebaseMessaging.onTokenRefresh.listen((newToken) {
      print('🔄 Token FCM renovado');
      registerToken(newToken);
    });
    
    return fcmToken;
  }
  
  /// Registrar token en el backend
  Future<bool> registerToken(String fcmToken) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/mobile/register-token/'),
        headers: _headers,
        body: json.encode({
          'fcm_token': fcmToken,
          'platform': 'android',
        }),
      );
      
      if (response.statusCode == 200 || response.statusCode == 201) {
        print('✅ Token registrado en backend');
        return true;
      }
      
      print('❌ Error registrando token: ${response.body}');
      return false;
      
    } catch (e) {
      print('❌ Error de red: $e');
      return false;
    }
  }
  
  /// Desregistrar token (logout)
  Future<bool> unregisterToken(String fcmToken) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/mobile/unregister-token/'),
        headers: _headers,
        body: json.encode({
          'fcm_token': fcmToken,
        }),
      );
      
      return response.statusCode == 200;
      
    } catch (e) {
      print('❌ Error desregistrando token: $e');
      return false;
    }
  }
  
  /// Configurar notificaciones en foreground
  void _configureForegroundNotifications() {
    FirebaseMessaging.onMessage.listen((RemoteMessage message) {
      print('📩 Notificación recibida (app abierta)');
      
      RemoteNotification? notification = message.notification;
      AndroidNotification? android = message.notification?.android;
      
      if (notification != null && android != null) {
        // Mostrar notificación local
        _localNotifications.show(
          notification.hashCode,
          notification.title,
          notification.body,
          NotificationDetails(
            android: AndroidNotificationDetails(
              'default',
              'Notificaciones Generales',
              channelDescription: 'Canal para notificaciones de la app',
              icon: '@mipmap/ic_launcher',
              importance: Importance.high,
              priority: Priority.high,
            ),
          ),
          payload: json.encode(message.data),
        );
      }
    });
  }
  
  /// Configurar handler cuando usuario toca notificación
  void _configureNotificationTapHandler() {
    // App abierta desde notificación
    FirebaseMessaging.onMessageOpenedApp.listen((RemoteMessage message) {
      print('📱 App abierta desde notificación');
      _handleNotificationTap(message.data);
    });
    
    // Verificar si app se abrió desde notificación (app cerrada)
    _firebaseMessaging.getInitialMessage().then((RemoteMessage? message) {
      if (message != null) {
        print('📱 App iniciada desde notificación');
        _handleNotificationTap(message.data);
      }
    });
  }
  
  /// Manejar navegación al tocar notificación
  void _handleNotificationTap(Map<String, dynamic> data) {
    // Aquí puedes navegar a una pantalla específica
    String? url = data['url'];
    String? appointmentId = data['appointment_id'];
    
    if (url != null) {
      print('🔗 Navegar a: $url');
      // Navigator.pushNamed(context, url);
    } else if (appointmentId != null) {
      print('📅 Abrir cita: $appointmentId');
      // Navigator.push(context, AppointmentDetailScreen(id: appointmentId));
    }
  }
}
```

---

### 3. Integrar en Login/Home

```dart
// lib/screens/home_screen.dart
import 'package:flutter/material.dart';
import '../services/notification_service.dart';

class HomeScreen extends StatefulWidget {
  final String userToken;
  
  const HomeScreen({Key? key, required this.userToken}) : super(key: key);
  
  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  String? _fcmToken;
  
  @override
  void initState() {
    super.initState();
    _initializeNotifications();
  }
  
  Future<void> _initializeNotifications() async {
    final notificationService = NotificationService(
      token: widget.userToken,
    );
    
    final fcmToken = await notificationService.initialize();
    
    setState(() {
      _fcmToken = fcmToken;
    });
    
    if (fcmToken != null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('✅ Notificaciones activadas'),
          backgroundColor: Colors.green,
        ),
      );
    }
  }
  
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('PsicoAdmin'),
      ),
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(Icons.notifications_active, size: 80, color: Colors.blue),
            SizedBox(height: 20),
            Text(
              _fcmToken != null
                  ? '✅ Notificaciones activas'
                  : '⏳ Configurando notificaciones...',
              style: TextStyle(fontSize: 18),
            ),
            if (_fcmToken != null) ...[
              SizedBox(height: 10),
              Text(
                'Token: ${_fcmToken!.substring(0, 20)}...',
                style: TextStyle(fontSize: 12, color: Colors.grey),
              ),
            ],
          ],
        ),
      ),
    );
  }
}
```

---

## 🔔 Testing

### 1. Testing Local (Flutter)

```bash
# Ejecutar app en modo debug
flutter run
```

**Verifica en consola:**
```
✅ Token FCM obtenido: dXm8K9hQ...
✅ Token registrado en backend
```

---

### 2. Testing de Envío (Backend)

Puedes enviar notificación desde Python shell:

```python
python manage.py shell
```

```python
from apps.notifications.fcm_service import send_fcm_notification

# Reemplaza con tu token FCM (copiado de la consola Flutter)
token = "dXm8K9hQ..."

result = send_fcm_notification(
    fcm_token=token,
    title="🧪 Test",
    body="Notificación de prueba desde Django",
    data={"test": "true"}
)

print(result)
```

---

### 3. Testing desde Firebase Console

1. Ve a **Firebase Console** → Tu proyecto
2. **Messaging** (Cloud Messaging)
3. Clic en **"Send your first message"**
4. **Título:** `Test desde Console`
5. **Texto:** `Esto es una prueba`
6. **Target:** Selecciona tu app
7. Clic **"Send test message"**
8. Pega tu **FCM token**
9. Clic **"Test"**

---

## 🔐 Seguridad

### Mejores Prácticas

1. **NUNCA** expongas el archivo de credenciales Firebase
   ```python
   # ❌ MAL - En repositorio público
   cred = credentials.Certificate('firebase-key.json')
   
   # ✅ BIEN - En variable de entorno o secrets
   cred_path = os.getenv('FIREBASE_CREDENTIALS_PATH')
   ```

2. **Valida permisos en backend**
   - Solo admins/professionals pueden enviar notificaciones
   - Usuarios solo pueden registrar su propio token

3. **Tokens FCM expiran**
   - Escucha `onTokenRefresh` en Flutter
   - Actualiza token en backend automáticamente

4. **Maneja datos sensibles**
   ```dart
   // ❌ MAL - Datos sensibles en notificación
   title: "Contraseña: 12345"
   
   // ✅ BIEN - Solo referencia
   title: "Nueva cita agendada"
   data: {"appointment_id": "123"}
   ```

---

## 📝 Próximos Pasos

1. **Aplicar migración:**
   ```bash
   python manage.py migrate notifications
   ```

2. **Probar registro de token** en Flutter

3. **Enviar notificación de prueba** desde backend

4. **Integrar con recordatorios de medicamentos**

5. **Agregar notificaciones para:**
   - Nueva cita
   - Recordatorio 1 hora antes de cita
   - Medicamento próximo
   - Mensaje nuevo del psicólogo

---

## ✅ Resumen de Configuración

| Componente | Estado |
|------------|--------|
| Firebase Project | ✅ Creado (`psicoadmin-94485`) |
| google-services.json | ✅ Descargado |
| Firebase Admin SDK | ✅ Instalado en backend |
| Modelo actualizado | ✅ `fcm_token`, `platform` |
| Endpoints FCM | ✅ 3 endpoints creados |
| Flutter Guide | ✅ Guía completa |

**🚀 Listo para implementar notificaciones móviles!**
