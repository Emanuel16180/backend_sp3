# Guía de Pagos con Stripe para Flutter Mobile (Android/iOS)

Esta guía documenta la implementación de pagos con Stripe usando **Payment Sheet** en aplicaciones Flutter nativas (Android/iOS). Es diferente de la implementación web/PWA.

## 📋 Tabla de Contenidos

1. [Diferencias con Web/PWA](#diferencias-con-webpwa)
2. [Configuración Inicial](#configuración-inicial)
3. [Endpoints del Backend](#endpoints-del-backend)
4. [Implementación Flutter](#implementación-flutter)
5. [Flujo de Pago de Citas](#flujo-de-pago-de-citas)
6. [Flujo de Compra de Planes](#flujo-de-compra-de-planes)
7. [Manejo de Errores](#manejo-de-errores)
8. [Testing](#testing)

---

## 🔄 Diferencias con Web/PWA

| Característica | Web/PWA | Mobile Nativo |
|---------------|---------|---------------|
| **Método** | Checkout Session | Payment Intent |
| **UI** | Página de Stripe | Payment Sheet nativo |
| **Redirect** | Sí (success_url) | No |
| **Confirmación** | Automática por webhook | Manual en app |
| **SDK** | JavaScript | flutter_stripe |

**¿Por qué no usar Checkout Session en mobile?**
- No hay redirección de navegador
- Mejor UX con UI nativa
- Mayor control del flujo de pago

---

## ⚙️ Configuración Inicial

### 1. Dependencias Flutter

```yaml
# pubspec.yaml
dependencies:
  flutter:
    sdk: flutter
  http: ^1.1.0
  flutter_stripe: ^10.1.1  # Stripe SDK para Flutter
  provider: ^6.1.1         # State management
```

### 2. Configuración Android

```xml
<!-- android/app/src/main/AndroidManifest.xml -->
<manifest>
    <application>
        <!-- ... -->
    </application>
    
    <!-- Permisos de Internet -->
    <uses-permission android:name="android.permission.INTERNET"/>
</manifest>
```

### 3. Configuración iOS

```ruby
# ios/Podfile
platform :ios, '13.0'
```

### 4. Inicializar Stripe en Flutter

```dart
// main.dart
import 'package:flutter/material.dart';
import 'package:flutter_stripe/flutter_stripe.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Obtener la publishable key desde tu API
  // En producción, obtenerla del backend
  Stripe.publishableKey = await _getStripePublishableKey();
  
  runApp(MyApp());
}

Future<String> _getStripePublishableKey() async {
  final response = await http.get(
    Uri.parse('https://api.psicoadmin.xyz/api/payments/stripe-public-key/'),
    headers: {'X-Tenant-Schema': 'bienestar'},
  );
  
  if (response.statusCode == 200) {
    final data = json.decode(response.body);
    return data['publishable_key'];
  }
  
  throw Exception('No se pudo obtener la clave de Stripe');
}
```

---

## 🔌 Endpoints del Backend

### 1. Crear Payment Intent para Cita

```http
POST /api/payments/mobile/create-intent-appointment/
X-Tenant-Schema: bienestar
Authorization: Token <user_token>
Content-Type: application/json

{
  "psychologist": 14,
  "appointment_date": "2025-11-25",
  "start_time": "10:00",
  "reason": "Consulta inicial"
}
```

**Respuesta exitosa:**
```json
{
  "client_secret": "pi_xxxxx_secret_xxxxx",
  "payment_intent_id": "pi_xxxxx",
  "appointment_id": 123,
  "amount": 50.00,
  "currency": "usd",
  "publishable_key": "pk_test_xxxxx"
}
```

### 2. Crear Payment Intent para Plan

```http
POST /api/payments/mobile/create-intent-plan/
X-Tenant-Schema: bienestar
Authorization: Token <user_token>
Content-Type: application/json

{
  "plan_id": 5
}
```

**Respuesta exitosa:**
```json
{
  "client_secret": "pi_xxxxx_secret_xxxxx",
  "payment_intent_id": "pi_xxxxx",
  "plan_id": 5,
  "amount": 200.00,
  "currency": "usd",
  "publishable_key": "pk_test_xxxxx"
}
```

### 3. Confirmar Pago

```http
POST /api/payments/mobile/confirm-payment/
X-Tenant-Schema: bienestar
Authorization: Token <user_token>
Content-Type: application/json

{
  "payment_intent_id": "pi_xxxxx"
}
```

**Respuesta exitosa (Cita):**
```json
{
  "success": true,
  "message": "Pago confirmado exitosamente",
  "appointment_id": 123,
  "status": "scheduled"
}
```

**Respuesta exitosa (Plan):**
```json
{
  "success": true,
  "message": "Plan activado exitosamente",
  "patient_plan_id": 45,
  "sessions_remaining": 10
}
```

---

## 📱 Implementación Flutter

### 1. Servicio de Pagos

```dart
// lib/services/payment_service.dart
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter_stripe/flutter_stripe.dart';
import 'package:http/http.dart' as http;

class PaymentService {
  static const String baseUrl = 'https://api.psicoadmin.xyz/api/payments';
  final String token;
  final String tenantSchema;

  PaymentService({
    required this.token,
    this.tenantSchema = 'bienestar',
  });

  Map<String, String> get _headers => {
    'Content-Type': 'application/json',
    'Authorization': 'Token $token',
    'X-Tenant-Schema': tenantSchema,
  };

  /// Pagar una cita
  Future<bool> payAppointment({
    required int psychologistId,
    required String appointmentDate,
    required String startTime,
    String reason = 'Consulta',
  }) async {
    try {
      // 1. Crear Payment Intent
      final intentResponse = await http.post(
        Uri.parse('$baseUrl/mobile/create-intent-appointment/'),
        headers: _headers,
        body: json.encode({
          'psychologist': psychologistId,
          'appointment_date': appointmentDate,
          'start_time': startTime,
          'reason': reason,
        }),
      );

      if (intentResponse.statusCode != 200) {
        final error = json.decode(intentResponse.body);
        throw Exception(error['error'] ?? 'Error al crear el pago');
      }

      final intentData = json.decode(intentResponse.body);
      final clientSecret = intentData['client_secret'];
      final paymentIntentId = intentData['payment_intent_id'];

      // 2. Inicializar Payment Sheet
      await Stripe.instance.initPaymentSheet(
        paymentSheetParameters: SetupPaymentSheetParameters(
          merchantDisplayName: 'PsicoAdmin',
          paymentIntentClientSecret: clientSecret,
          style: ThemeMode.system,
          billingDetails: BillingDetails(
            // Opcional: prellenar datos del usuario
          ),
        ),
      );

      // 3. Presentar Payment Sheet
      await Stripe.instance.presentPaymentSheet();

      // 4. Si llega aquí, el pago fue exitoso
      // Confirmar con el backend
      final confirmResponse = await http.post(
        Uri.parse('$baseUrl/mobile/confirm-payment/'),
        headers: _headers,
        body: json.encode({
          'payment_intent_id': paymentIntentId,
        }),
      );

      if (confirmResponse.statusCode == 200) {
        return true;
      }

      throw Exception('Error al confirmar el pago');
      
    } on StripeException catch (e) {
      // Usuario canceló o error de Stripe
      print('Error de Stripe: ${e.error.message}');
      rethrow;
    } catch (e) {
      print('Error general: $e');
      rethrow;
    }
  }

  /// Comprar un plan
  Future<bool> purchasePlan({required int planId}) async {
    try {
      // 1. Crear Payment Intent
      final intentResponse = await http.post(
        Uri.parse('$baseUrl/mobile/create-intent-plan/'),
        headers: _headers,
        body: json.encode({
          'plan_id': planId,
        }),
      );

      if (intentResponse.statusCode != 200) {
        final error = json.decode(intentResponse.body);
        throw Exception(error['error'] ?? 'Error al crear el pago');
      }

      final intentData = json.decode(intentResponse.body);
      final clientSecret = intentData['client_secret'];
      final paymentIntentId = intentData['payment_intent_id'];

      // 2. Inicializar Payment Sheet
      await Stripe.instance.initPaymentSheet(
        paymentSheetParameters: SetupPaymentSheetParameters(
          merchantDisplayName: 'PsicoAdmin',
          paymentIntentClientSecret: clientSecret,
          style: ThemeMode.system,
        ),
      );

      // 3. Presentar Payment Sheet
      await Stripe.instance.presentPaymentSheet();

      // 4. Confirmar con el backend
      final confirmResponse = await http.post(
        Uri.parse('$baseUrl/mobile/confirm-payment/'),
        headers: _headers,
        body: json.encode({
          'payment_intent_id': paymentIntentId,
        }),
      );

      if (confirmResponse.statusCode == 200) {
        return true;
      }

      throw Exception('Error al confirmar el pago');
      
    } on StripeException catch (e) {
      print('Error de Stripe: ${e.error.message}');
      rethrow;
    } catch (e) {
      print('Error general: $e');
      rethrow;
    }
  }
}
```

### 2. Widget de Pago de Cita

```dart
// lib/widgets/appointment_payment_button.dart
import 'package:flutter/material.dart';
import 'package:flutter_stripe/flutter_stripe.dart';
import '../services/payment_service.dart';

class AppointmentPaymentButton extends StatefulWidget {
  final int psychologistId;
  final String appointmentDate;
  final String startTime;
  final double amount;
  final VoidCallback onSuccess;

  const AppointmentPaymentButton({
    Key? key,
    required this.psychologistId,
    required this.appointmentDate,
    required this.startTime,
    required this.amount,
    required this.onSuccess,
  }) : super(key: key);

  @override
  State<AppointmentPaymentButton> createState() => _AppointmentPaymentButtonState();
}

class _AppointmentPaymentButtonState extends State<AppointmentPaymentButton> {
  bool _isLoading = false;

  Future<void> _handlePayment() async {
    setState(() => _isLoading = true);

    try {
      final paymentService = PaymentService(
        token: 'YOUR_USER_TOKEN', // Obtener del state management
      );

      final success = await paymentService.payAppointment(
        psychologistId: widget.psychologistId,
        appointmentDate: widget.appointmentDate,
        startTime: widget.startTime,
      );

      if (success) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('✅ Pago exitoso. Cita confirmada'),
            backgroundColor: Colors.green,
          ),
        );
        widget.onSuccess();
      }
      
    } on StripeException catch (e) {
      // Usuario canceló
      if (e.error.code == FailureCode.Canceled) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Pago cancelado')),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error: ${e.error.message}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error al procesar el pago'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: _isLoading ? null : _handlePayment,
      style: ElevatedButton.styleFrom(
        padding: EdgeInsets.symmetric(horizontal: 32, vertical: 16),
        backgroundColor: Colors.blue,
      ),
      child: _isLoading
          ? SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
              ),
            )
          : Text(
              'Pagar \$${widget.amount.toStringAsFixed(2)}',
              style: TextStyle(fontSize: 16, color: Colors.white),
            ),
    );
  }
}
```

### 3. Screen de Confirmación de Cita

```dart
// lib/screens/appointment_confirmation_screen.dart
import 'package:flutter/material.dart';
import '../widgets/appointment_payment_button.dart';

class AppointmentConfirmationScreen extends StatelessWidget {
  final int psychologistId;
  final String psychologistName;
  final String appointmentDate;
  final String startTime;
  final double consultationFee;

  const AppointmentConfirmationScreen({
    Key? key,
    required this.psychologistId,
    required this.psychologistName,
    required this.appointmentDate,
    required this.startTime,
    required this.consultationFee,
  }) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Confirmar Cita'),
      ),
      body: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Resumen de la Cita',
              style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
            ),
            SizedBox(height: 24),
            
            _buildInfoRow('Profesional', psychologistName),
            _buildInfoRow('Fecha', appointmentDate),
            _buildInfoRow('Hora', startTime),
            _buildInfoRow(
              'Monto',
              '\$${consultationFee.toStringAsFixed(2)}',
              isAmount: true,
            ),
            
            Spacer(),
            
            AppointmentPaymentButton(
              psychologistId: psychologistId,
              appointmentDate: appointmentDate,
              startTime: startTime,
              amount: consultationFee,
              onSuccess: () {
                Navigator.of(context).pushReplacementNamed('/appointments');
              },
            ),
            
            SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value, {bool isAmount = false}) {
    return Padding(
      padding: EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: TextStyle(fontSize: 16, color: Colors.grey[600]),
          ),
          Text(
            value,
            style: TextStyle(
              fontSize: isAmount ? 20 : 16,
              fontWeight: isAmount ? FontWeight.bold : FontWeight.normal,
              color: isAmount ? Colors.blue : Colors.black,
            ),
          ),
        ],
      ),
    );
  }
}
```

### 4. Widget de Compra de Plan

```dart
// lib/widgets/plan_purchase_button.dart
import 'package:flutter/material.dart';
import 'package:flutter_stripe/flutter_stripe.dart';
import '../services/payment_service.dart';

class PlanPurchaseButton extends StatefulWidget {
  final int planId;
  final String planName;
  final double price;
  final VoidCallback onSuccess;

  const PlanPurchaseButton({
    Key? key,
    required this.planId,
    required this.planName,
    required this.price,
    required this.onSuccess,
  }) : super(key: key);

  @override
  State<PlanPurchaseButton> createState() => _PlanPurchaseButtonState();
}

class _PlanPurchaseButtonState extends State<PlanPurchaseButton> {
  bool _isLoading = false;

  Future<void> _handlePurchase() async {
    setState(() => _isLoading = true);

    try {
      final paymentService = PaymentService(
        token: 'YOUR_USER_TOKEN', // Obtener del state management
      );

      final success = await paymentService.purchasePlan(
        planId: widget.planId,
      );

      if (success) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('✅ Plan "${widget.planName}" activado'),
            backgroundColor: Colors.green,
          ),
        );
        widget.onSuccess();
      }
      
    } on StripeException catch (e) {
      if (e.error.code == FailureCode.Canceled) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Compra cancelada')),
        );
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Error: ${e.error.message}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error al procesar la compra'),
          backgroundColor: Colors.red,
        ),
      );
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return ElevatedButton(
      onPressed: _isLoading ? null : _handlePurchase,
      style: ElevatedButton.styleFrom(
        padding: EdgeInsets.symmetric(horizontal: 32, vertical: 16),
        backgroundColor: Colors.green,
      ),
      child: _isLoading
          ? SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
              ),
            )
          : Text(
              'Comprar Plan - \$${widget.price.toStringAsFixed(2)}',
              style: TextStyle(fontSize: 16, color: Colors.white),
            ),
    );
  }
}
```

---

## 🔄 Flujo de Pago de Citas

```
1. Usuario selecciona profesional, fecha y hora
   ↓
2. App llama a /mobile/create-intent-appointment/
   ↓
3. Backend crea cita preliminar (pending, is_paid=False)
   ↓
4. Backend crea Payment Intent en Stripe
   ↓
5. Backend retorna client_secret
   ↓
6. Flutter inicializa Payment Sheet con client_secret
   ↓
7. Usuario ingresa datos de tarjeta en Payment Sheet nativo
   ↓
8. Stripe procesa el pago
   ↓
9. Si éxito: Flutter llama a /mobile/confirm-payment/
   ↓
10. Backend actualiza cita (is_paid=True, status=scheduled)
    ↓
11. Backend crea PaymentTransaction
    ↓
12. App muestra confirmación
```

---

## 💳 Flujo de Compra de Planes

```
1. Usuario selecciona un plan
   ↓
2. App llama a /mobile/create-intent-plan/
   ↓
3. Backend valida que el usuario no tenga el plan activo
   ↓
4. Backend crea Payment Intent en Stripe
   ↓
5. Backend retorna client_secret
   ↓
6. Flutter inicializa Payment Sheet
   ↓
7. Usuario ingresa datos de tarjeta
   ↓
8. Stripe procesa el pago
   ↓
9. Si éxito: Flutter llama a /mobile/confirm-payment/
   ↓
10. Backend crea PatientPlan (is_active=True)
    ↓
11. Backend crea PaymentTransaction
    ↓
12. App muestra plan activado
```

---

## ⚠️ Manejo de Errores

### Errores Comunes de Stripe

```dart
try {
  await Stripe.instance.presentPaymentSheet();
} on StripeException catch (e) {
  switch (e.error.code) {
    case FailureCode.Canceled:
      // Usuario canceló
      print('Pago cancelado por el usuario');
      break;
      
    case FailureCode.Failed:
      // Pago rechazado
      print('Pago rechazado: ${e.error.message}');
      break;
      
    case FailureCode.Timeout:
      // Timeout
      print('Tiempo de espera agotado');
      break;
      
    default:
      print('Error: ${e.error.message}');
  }
}
```

### Errores del Backend

```dart
final response = await http.post(url, headers: headers, body: body);

if (response.statusCode != 200) {
  final error = json.decode(response.body);
  
  // Manejar errores específicos
  if (error['error'] == 'Ya tienes este plan activo') {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Plan Activo'),
        content: Text('Ya tienes este plan activado'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('OK'),
          ),
        ],
      ),
    );
  }
}
```

---

## 🧪 Testing

### Tarjetas de Prueba (Stripe Test Mode)

| Número | Resultado |
|--------|-----------|
| 4242 4242 4242 4242 | Pago exitoso |
| 4000 0000 0000 9995 | Pago rechazado |
| 4000 0025 0000 3155 | Requiere autenticación 3D Secure |

**Datos de prueba:**
- **Fecha de expiración:** Cualquier fecha futura (ej: 12/25)
- **CVC:** Cualquier 3 dígitos (ej: 123)
- **ZIP:** Cualquier código postal

### Test Manual

1. Ejecuta la app en modo debug
2. Selecciona crear una cita
3. Usa tarjeta `4242 4242 4242 4242`
4. Verifica que la cita se crea con `is_paid=True`
5. Verifica en Stripe Dashboard que el Payment Intent aparece

---

## 🔐 Seguridad

### Mejores Prácticas

1. **NUNCA** guardes el token de usuario en código
   ```dart
   // ❌ MAL
   final token = "abc123";
   
   // ✅ BIEN
   final token = await SecureStorage.read(key: 'auth_token');
   ```

2. **Usa HTTPS** siempre
   ```dart
   const String baseUrl = 'https://api.psicoadmin.xyz'; // ✅
   // NUNCA http:// en producción
   ```

3. **Valida en el backend** siempre
   - El backend valida que el usuario sea el correcto
   - El backend verifica el estado del Payment Intent
   - El backend previene duplicados

4. **Maneja estados correctamente**
   ```dart
   // Guardar el appointment_id localmente
   // Por si el usuario cierra la app durante el pago
   await prefs.setInt('pending_appointment_id', appointmentId);
   ```

---

## 📝 Notas Importantes

1. **Payment Sheet vs Checkout Session**
   - Payment Sheet: Para apps mobile nativas ✅
   - Checkout Session: Para web/PWA ✅
   - Son métodos diferentes, NO intercambiables

2. **Confirmación Manual**
   - En mobile, debes llamar a `/mobile/confirm-payment/`
   - El webhook NO es suficiente como único método de confirmación
   - La app confirma inmediatamente después del pago exitoso

3. **Idempotencia**
   - El backend valida si una cita ya fue pagada
   - Previene cargos duplicados
   - Si vuelves a confirmar, retorna la cita existente

4. **Testing**
   - Usa Stripe Test Mode durante desarrollo
   - Cambia a claves de producción al publicar
   - NUNCA mezcles claves de test y producción

5. **Webhooks**
   - Los webhooks siguen funcionando como respaldo
   - Útil si la app se cierra antes de confirmar
   - Procesados de forma asíncrona por el backend

---

## 🚀 Deploy a Producción

### 1. Cambiar a Claves de Producción

```dart
// Obtener desde variables de entorno o backend
Stripe.publishableKey = 'pk_live_xxxxx'; // ⚠️ Clave de producción
```

### 2. Configurar Webhooks en Stripe (Opcional)

1. Ve a Stripe Dashboard → Webhooks
2. Añade endpoint: `https://api.psicoadmin.xyz/api/payments/stripe-webhook/`
3. Selecciona eventos:
   - `payment_intent.succeeded`
   - `payment_intent.payment_failed`

**Nota:** Los webhooks son opcionales en mobile porque la confirmación se hace desde la app. Sin embargo, son útiles como respaldo por si la app se cierra antes de confirmar.

### 3. Verificar en Producción

1. Hacer una compra de prueba pequeña (mínimo permitido)
2. Verificar en Stripe Dashboard que el Payment Intent aparece como `succeeded`
3. Verificar que la cita se marca como `is_paid=True` y `status=scheduled`
4. Verificar que se crea el registro en `PaymentTransaction`
5. Probar con tarjeta 3D Secure para autenticación completa

---

## 📞 Soporte

Si tienes problemas:

1. Revisa los logs de Stripe Dashboard
2. Verifica los logs del backend en Render
3. Usa `print()` para debug en Flutter
4. Consulta [Stripe Docs](https://stripe.com/docs/payments/accept-a-payment?platform=flutter)

---

**✅ Implementación completa de pagos mobile con Flutter y Stripe**
