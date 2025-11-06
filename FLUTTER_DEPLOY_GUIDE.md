# 📱 CONFIGURACIÓN DEL FRONTEND FLUTTER

## 🎯 PASO 1: Obtener URL del Backend

**Primero necesitas la URL de Render.com:**

Ve al Dashboard de Render y copia tu URL. Será algo como:
```
https://psico-admin-api.onrender.com
```

O si configuraste dominios personalizados:
```
https://api.psicoadmin.xyz
```

---

## 📝 PASO 2: Actualizar Configuración de la API

### Archivo: `lib/config/api_config.dart`

```dart
class ApiConfig {
  // ✅ URL de Producción (Render.com)
  static const String prodBaseUrl = 'https://TU-URL-DE-RENDER.onrender.com';
  
  // O si usas tu dominio:
  // static const String prodBaseUrl = 'https://api.psicoadmin.xyz';
  
  // 🔧 URL de Desarrollo (tu máquina local)
  static const String devBaseUrl = 'http://192.168.0.12:8000';
  
  // Selecciona automáticamente según el modo
  static String get baseUrl {
    const bool isProduction = bool.fromEnvironment('dart.vm.product');
    return isProduction ? prodBaseUrl : devBaseUrl;
  }
  
  // Endpoints específicos
  static String get authUrl => '$baseUrl/api/auth';
  static String get usersUrl => '$baseUrl/api/users';
  static String get appointmentsUrl => '$baseUrl/api/appointments';
  static String get professionalsUrl => '$baseUrl/api/professionals';
  static String get chatUrl => '$baseUrl/api/chat';
  static String get paymentsUrl => '$baseUrl/api/payments';
  
  // Headers para multi-tenant
  static Map<String, String> getHeaders({String? tenantSchema}) {
    final headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    
    if (tenantSchema != null) {
      headers['X-Tenant-Schema'] = tenantSchema;
    }
    
    return headers;
  }
}
```

---

## 🔧 PASO 3: Configurar Tenant en el Login

### Archivo: `lib/services/auth_service.dart`

Asegúrate de que tu servicio de autenticación incluya el header del tenant:

```dart
Future<bool> login(String email, String password, String tenantSchema) async {
  try {
    final response = await http.post(
      Uri.parse('${ApiConfig.authUrl}/login/'),
      headers: ApiConfig.getHeaders(tenantSchema: tenantSchema),
      body: jsonEncode({
        'email': email,
        'password': password,
      }),
    );
    
    if (response.statusCode == 200) {
      final data = jsonDecode(response.body);
      // Guardar token y tenant
      await _storage.write(key: 'auth_token', value: data['token']);
      await _storage.write(key: 'tenant_schema', value: tenantSchema);
      return true;
    }
    
    return false;
  } catch (e) {
    print('Error en login: $e');
    return false;
  }
}
```

---

## 🏥 PASO 4: Selector de Clínica en la App

### Archivo: `lib/screens/clinic_selector_screen.dart`

```dart
import 'package:flutter/material.dart';

class ClinicSelectorScreen extends StatelessWidget {
  const ClinicSelectorScreen({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
            colors: [Colors.blue.shade400, Colors.purple.shade600],
          ),
        ),
        child: SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Logo
                Icon(
                  Icons.medical_services,
                  size: 80,
                  color: Colors.white,
                ),
                SizedBox(height: 24),
                
                // Título
                Text(
                  'Selecciona tu Clínica',
                  style: TextStyle(
                    fontSize: 28,
                    fontWeight: FontWeight.bold,
                    color: Colors.white,
                  ),
                ),
                SizedBox(height: 48),
                
                // Card Bienestar
                _ClinicCard(
                  name: 'Clínica Bienestar',
                  schema: 'bienestar',
                  icon: Icons.spa,
                  color: Colors.green,
                  onTap: () => _navigateToLogin(context, 'bienestar'),
                ),
                
                SizedBox(height: 16),
                
                // Card Mindcare
                _ClinicCard(
                  name: 'Clínica Mindcare',
                  schema: 'mindcare',
                  icon: Icons.psychology,
                  color: Colors.blue,
                  onTap: () => _navigateToLogin(context, 'mindcare'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
  
  void _navigateToLogin(BuildContext context, String tenantSchema) {
    Navigator.pushNamed(
      context,
      '/login',
      arguments: tenantSchema,
    );
  }
}

class _ClinicCard extends StatelessWidget {
  final String name;
  final String schema;
  final IconData icon;
  final Color color;
  final VoidCallback onTap;

  const _ClinicCard({
    required this.name,
    required this.schema,
    required this.icon,
    required this.color,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 8,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(16),
        child: Padding(
          padding: const EdgeInsets.all(24.0),
          child: Row(
            children: [
              Container(
                padding: EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(
                  icon,
                  size: 40,
                  color: color,
                ),
              ),
              SizedBox(width: 20),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      name,
                      style: TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    SizedBox(height: 4),
                    Text(
                      'Toca para continuar',
                      style: TextStyle(
                        fontSize: 14,
                        color: Colors.grey.shade600,
                      ),
                    ),
                  ],
                ),
              ),
              Icon(
                Icons.arrow_forward_ios,
                color: Colors.grey.shade400,
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

## 📱 PASO 5: Actualizar main.dart

```dart
void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Psico Admin',
      theme: ThemeData(
        primarySwatch: Colors.blue,
        visualDensity: VisualDensity.adaptivePlatformDensity,
      ),
      debugShowCheckedModeBanner: false,
      
      // Rutas
      initialRoute: '/clinic-selector',
      routes: {
        '/clinic-selector': (context) => ClinicSelectorScreen(),
        '/login': (context) => LoginScreen(),
        '/home': (context) => HomeScreen(),
        // ... otras rutas
      },
    );
  }
}
```

---

## 🌐 PASO 6: Variables de Entorno para Build

### Android - `android/app/build.gradle`

Agrega al final del archivo:

```gradle
android {
    // ... configuración existente
    
    buildTypes {
        release {
            // ... configuración existente
            
            // Variables de entorno
            buildConfigField "String", "API_BASE_URL", "\"https://TU-URL-DE-RENDER.onrender.com\""
        }
        
        debug {
            buildConfigField "String", "API_BASE_URL", "\"http://10.0.2.2:8000\""
        }
    }
}
```

### iOS - `ios/Runner/Info.plist`

Agrega dentro de `<dict>`:

```xml
<key>API_BASE_URL</key>
<string>https://TU-URL-DE-RENDER.onrender.com</string>
```

---

## 🔐 PASO 7: Credenciales de Prueba

Comparte estas credenciales con el equipo frontend:

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

```
(Usa las mismas credenciales con el tenant "mindcare")
```

---

## 📦 PASO 8: Build para Producción

### Android APK:
```bash
flutter build apk --release
```

### Android App Bundle (para Play Store):
```bash
flutter build appbundle --release
```

### iOS:
```bash
flutter build ios --release
```

---

## 🚀 OPCIONAL: Desplegar Web en Vercel

Si tu app Flutter soporta Web:

### 1. Build Web:
```bash
flutter build web --release
```

### 2. Crear `vercel.json` en la raíz:
```json
{
  "version": 2,
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/index.html"
    }
  ]
}
```

### 3. Desplegar en Vercel:
```bash
# Instalar Vercel CLI
npm i -g vercel

# En la carpeta del proyecto Flutter
cd build/web

# Desplegar
vercel --prod
```

### 4. Configurar Dominio en Vercel:
- Ve a tu proyecto en Vercel Dashboard
- Settings → Domains
- Agrega: `app.psicoadmin.xyz`
- Configura en tu DNS:
  - **CNAME** `app` → `cname.vercel-dns.com`

---

## ✅ CHECKLIST FINAL

- [ ] Actualizar `api_config.dart` con URL de producción
- [ ] Agregar selector de clínicas
- [ ] Configurar headers con X-Tenant-Schema
- [ ] Probar login con ambos tenants
- [ ] Build APK/iOS
- [ ] (Opcional) Deploy web en Vercel
- [ ] Configurar dominios personalizados

---

## 🔗 URLs Finales

Una vez configurado todo:

```
Backend API: https://api.psicoadmin.xyz
Bienestar: https://bienestar.psicoadmin.xyz
Mindcare: https://mindcare.psicoadmin.xyz
App Web: https://app.psicoadmin.xyz (si usas Vercel)
```

---

## 📞 Soporte

Si hay errores de CORS o conectividad:
1. Verifica que `ALLOWED_HOSTS` incluya tu dominio en el backend
2. Verifica que `CORS_ALLOWED_ORIGINS` incluya la URL de la app
3. Asegúrate de usar HTTPS en producción

---

**¿Ya tienes la URL de Render? Pásame la URL y actualizo el archivo con tu dominio específico.** 🚀
