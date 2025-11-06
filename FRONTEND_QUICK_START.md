# 🎯 GUÍA RÁPIDA PARA EL EQUIPO FRONTEND

## ✅ BACKEND DESPLEGADO Y FUNCIONANDO

**URL Base de la API**: `https://api.psicoadmin.xyz`

---

## 🔑 CREDENCIALES DE PRUEBA

### Tenant: **bienestar**

```
Admin:
  Email: admin@bienestar.com
  Password: admin123

Psicóloga:
  Email: dra.martinez@bienestar.com
  Password: demo123

Psiquiatra:
  Email: dr.valverde@bienestar.com
  Password: demo123

Paciente:
  Email: juan.perez@example.com
  Password: demo123
```

### Tenant: **mindcare**
*(Mismas credenciales, solo cambia el tenant en el header)*

---

## 📝 CONFIGURACIÓN FLUTTER - PASO A PASO

### 1️⃣ Actualizar `lib/config/api_config.dart`

```dart
class ApiConfig {
  // ✅ Producción
  static const String prodBaseUrl = 'https://api.psicoadmin.xyz';
  
  // 🔧 Desarrollo
  static const String devBaseUrl = 'http://192.168.0.12:8000';
  
  static String get baseUrl {
    const bool isProduction = bool.fromEnvironment('dart.vm.product');
    return isProduction ? prodBaseUrl : devBaseUrl;
  }
  
  // Headers con tenant
  static Map<String, String> headers(String tenantSchema, {String? token}) {
    final headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'X-Tenant-Schema': tenantSchema,
    };
    
    if (token != null) {
      headers['Authorization'] = 'Token $token';
    }
    
    return headers;
  }
}
```

### 2️⃣ Ejemplo de Login

```dart
import 'dart:convert';
import 'package:http/http.dart' as http;

Future<Map<String, dynamic>?> login(
  String email,
  String password,
  String tenantSchema,
) async {
  try {
    final response = await http.post(
      Uri.parse('https://api.psicoadmin.xyz/api/auth/login/'),
      headers: {
        'Content-Type': 'application/json',
        'X-Tenant-Schema': tenantSchema,
      },
      body: jsonEncode({
        'email': email,
        'password': password,
      }),
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    
    print('Error: ${response.statusCode} - ${response.body}');
    return null;
  } catch (e) {
    print('Exception: $e');
    return null;
  }
}

// Uso:
void main() async {
  final result = await login(
    'admin@bienestar.com',
    'admin123',
    'bienestar',
  );
  
  if (result != null) {
    print('Token: ${result['token']}');
    print('User: ${result['user']}');
  }
}
```

### 3️⃣ Ejemplo de Request Autenticado

```dart
Future<Map<String, dynamic>?> getUserProfile(
  String token,
  String tenantSchema,
) async {
  try {
    final response = await http.get(
      Uri.parse('https://api.psicoadmin.xyz/api/users/me/'),
      headers: {
        'Authorization': 'Token $token',
        'X-Tenant-Schema': tenantSchema,
        'Content-Type': 'application/json',
      },
    );
    
    if (response.statusCode == 200) {
      return jsonDecode(response.body);
    }
    
    return null;
  } catch (e) {
    print('Exception: $e');
    return null;
  }
}
```

---

## 🏥 SELECTOR DE CLÍNICA

Agrega esta pantalla al inicio de tu app:

```dart
// lib/screens/clinic_selector.dart

import 'package:flutter/material.dart';

class ClinicSelectorScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [Colors.blue, Colors.purple],
          ),
        ),
        child: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                'Selecciona tu Clínica',
                style: TextStyle(
                  fontSize: 32,
                  color: Colors.white,
                  fontWeight: FontWeight.bold,
                ),
              ),
              SizedBox(height: 50),
              
              // Bienestar
              ElevatedButton(
                onPressed: () {
                  Navigator.pushNamed(
                    context,
                    '/login',
                    arguments: 'bienestar',
                  );
                },
                child: Text('Clínica Bienestar'),
                style: ElevatedButton.styleFrom(
                  padding: EdgeInsets.symmetric(horizontal: 50, vertical: 20),
                  textStyle: TextStyle(fontSize: 18),
                ),
              ),
              
              SizedBox(height: 20),
              
              // Mindcare
              ElevatedButton(
                onPressed: () {
                  Navigator.pushNamed(
                    context,
                    '/login',
                    arguments: 'mindcare',
                  );
                },
                child: Text('Clínica Mindcare'),
                style: ElevatedButton.styleFrom(
                  padding: EdgeInsets.symmetric(horizontal: 50, vertical: 20),
                  textStyle: TextStyle(fontSize: 18),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
```

---

## 🔧 ENDPOINTS DISPONIBLES

### Autenticación
```
POST /api/auth/register/         - Registro
POST /api/auth/login/            - Login
POST /api/auth/logout/           - Logout
POST /api/auth/password/reset/   - Reset password
```

### Usuarios
```
GET    /api/users/me/            - Perfil actual
PUT    /api/users/me/            - Actualizar perfil
GET    /api/users/               - Listar usuarios (admin)
GET    /api/users/{id}/          - Detalle usuario
```

### Profesionales
```
GET    /api/professionals/                    - Listar profesionales
GET    /api/professionals/{id}/               - Detalle profesional
GET    /api/professionals/{id}/availability/  - Disponibilidad
```

### Citas
```
GET    /api/appointments/           - Mis citas
POST   /api/appointments/           - Crear cita
GET    /api/appointments/{id}/      - Detalle cita
PATCH  /api/appointments/{id}/      - Actualizar cita
POST   /api/appointments/{id}/cancel/ - Cancelar cita
```

### Chat
```
GET    /api/chat/conversations/     - Mis conversaciones
POST   /api/chat/conversations/     - Nueva conversación
GET    /api/chat/messages/          - Mensajes
POST   /api/chat/messages/          - Enviar mensaje
```

### Pagos
```
GET    /api/payments/appointments/{id}/status/  - Estado de pago
POST   /api/payments/stripe/create-intent/      - Crear intención de pago
POST   /api/payments/stripe/confirm/            - Confirmar pago
```

---

## ⚠️ IMPORTANTE: Headers Requeridos

**TODOS los requests deben incluir:**

```dart
{
  'Content-Type': 'application/json',
  'X-Tenant-Schema': 'bienestar',  // o 'mindcare'
  'Authorization': 'Token <tu_token>',  // después del login
}
```

---

## 🧪 PROBAR LA API

### Con cURL:

```bash
# Login
curl -X POST https://api.psicoadmin.xyz/api/auth/login/ \
  -H "Content-Type: application/json" \
  -H "X-Tenant-Schema: bienestar" \
  -d '{"email": "admin@bienestar.com", "password": "admin123"}'

# Obtener perfil
curl https://api.psicoadmin.xyz/api/users/me/ \
  -H "Authorization: Token TU_TOKEN_AQUI" \
  -H "X-Tenant-Schema: bienestar"
```

### Con Postman/Insomnia:

1. **Base URL**: `https://api.psicoadmin.xyz`
2. **Headers** (en todas las requests):
   - `Content-Type: application/json`
   - `X-Tenant-Schema: bienestar`
   - `Authorization: Token <token>` (después del login)

---

## 📱 BUILD DE PRODUCCIÓN

### Android:
```bash
flutter build apk --release
# El APK estará en: build/app/outputs/flutter-apk/app-release.apk
```

### iOS:
```bash
flutter build ios --release
# Luego abre Xcode y archive
```

---

## 🌐 URLS FINALES

```
API Base:    https://api.psicoadmin.xyz
Bienestar:   https://bienestar.psicoadmin.xyz
Mindcare:    https://mindcare.psicoadmin.xyz
Admin:       https://api.psicoadmin.xyz/admin
```

---

## 🆘 ERRORES COMUNES

### ❌ Error: "Dominio no encontrado"
**Solución**: Asegúrate de incluir el header `X-Tenant-Schema`

### ❌ Error: "Authentication credentials were not provided"
**Solución**: Incluye el header `Authorization: Token <token>`

### ❌ Error: "CORS policy"
**Solución**: El backend ya tiene CORS configurado. Verifica que uses HTTPS en producción.

### ❌ Error: "Connection refused"
**Solución**: 
- En desarrollo: Usa `http://10.0.2.2:8000` (Android emulator)
- En producción: Usa `https://api.psicoadmin.xyz`

---

## 📞 DOCUMENTACIÓN COMPLETA

Para documentación completa de todos los endpoints:
👉 **Ver archivo: `API_DOCUMENTATION.md`** en el repositorio del backend

---

## ✅ CHECKLIST

- [ ] Actualizar `api_config.dart` con la URL de producción
- [ ] Implementar selector de clínicas
- [ ] Agregar header `X-Tenant-Schema` a todos los requests
- [ ] Probar login con ambos tenants
- [ ] Probar endpoints principales
- [ ] Build APK/iOS de prueba
- [ ] ¡Deploy! 🚀

---

**¿Dudas? Contacta al equipo backend.** 💬
