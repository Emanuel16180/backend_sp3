# Script para probar notificaciones FCM en Flutter
# Asegúrate de que el servidor Django esté corriendo (python manage.py runserver)

Write-Host "=== PRUEBA DE NOTIFICACIONES FCM - FLUTTER ===" -ForegroundColor Cyan
Write-Host ""

# Configuración
$baseUrl = "http://127.0.0.1:8000"
$tenantSchema = "bienestar"

# Paso 1: Login como usuario de prueba
Write-Host "📝 Paso 1: Login como usuario..." -ForegroundColor Yellow

$loginData = @{
    email = "ana.torres@example.com"
    password = "demo123"
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Uri "$baseUrl/api/auth/login/" `
        -Method POST `
        -Headers @{
            "Content-Type" = "application/json"
            "X-Tenant-Schema" = $tenantSchema
        } `
        -Body $loginData
    
    $token = $loginResponse.token
    $userId = $loginResponse.user.id
    
    Write-Host "   ✅ Login exitoso" -ForegroundColor Green
    Write-Host "   👤 Usuario: $($loginResponse.user.first_name) $($loginResponse.user.last_name)" -ForegroundColor Gray
    Write-Host "   🆔 User ID: $userId" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "   ❌ Error en login: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "   💡 Verifica que el servidor esté corriendo" -ForegroundColor Yellow
    exit 1
}

# Paso 2: Solicitar FCM Token
Write-Host "📝 Paso 2: Ingresa el FCM Token de tu dispositivo Flutter" -ForegroundColor Yellow
Write-Host "   (Cópialo de la consola de Flutter cuando ejecutes la app)" -ForegroundColor Gray
Write-Host ""
$fcmToken = Read-Host "   🔑 FCM Token"

if ([string]::IsNullOrWhiteSpace($fcmToken)) {
    Write-Host ""
    Write-Host "❌ Token vacío. Debes ejecutar la app Flutter primero." -ForegroundColor Red
    Write-Host ""
    Write-Host "INSTRUCCIONES:" -ForegroundColor Yellow
    Write-Host "1. Ejecuta: cd flutter_psicenter && flutter run" -ForegroundColor White
    Write-Host "2. Busca en la consola: '✅ Token FCM obtenido: ...'" -ForegroundColor White
    Write-Host "3. Copia el token y pégalo aquí" -ForegroundColor White
    Write-Host ""
    exit 1
}

Write-Host ""

# Paso 3: Registrar token en backend (opcional, la app ya lo hace)
Write-Host "📝 Paso 3: Verificando registro del token..." -ForegroundColor Yellow

$registerData = @{
    fcm_token = $fcmToken
    platform = "android"
} | ConvertTo-Json

try {
    $registerResponse = Invoke-RestMethod -Uri "$baseUrl/api/notifications/mobile/register-token/" `
        -Method POST `
        -Headers @{
            "Content-Type" = "application/json"
            "Authorization" = "Token $token"
            "X-Tenant-Schema" = $tenantSchema
        } `
        -Body $registerData
    
    Write-Host "   ✅ Token registrado: $($registerResponse.message)" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "   ⚠️  Posible error al registrar: $($_.Exception.Message)" -ForegroundColor Yellow
    Write-Host "   (Puede que ya esté registrado, continuamos...)" -ForegroundColor Gray
    Write-Host ""
}

# Paso 4: Enviar notificación de prueba
Write-Host "📝 Paso 4: Enviando notificación de prueba..." -ForegroundColor Yellow

$notificationData = @{
    user_id = $userId
    title = "🎉 ¡Notificación de Prueba!"
    body = "Si ves esto, las notificaciones FCM están funcionando perfectamente en tu app Flutter"
    data = @{
        type = "test"
        timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    }
} | ConvertTo-Json

try {
    $sendResponse = Invoke-RestMethod -Uri "$baseUrl/api/notifications/mobile/send/" `
        -Method POST `
        -Headers @{
            "Content-Type" = "application/json"
            "Authorization" = "Token $token"
            "X-Tenant-Schema" = $tenantSchema
        } `
        -Body $notificationData
    
    Write-Host ""
    Write-Host "   ✅ ¡NOTIFICACIÓN ENVIADA EXITOSAMENTE!" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Resultado:" -ForegroundColor Cyan
    Write-Host "   • Total usuarios: $($sendResponse.total_users)" -ForegroundColor Gray
    Write-Host "   • Enviadas: $($sendResponse.sent)" -ForegroundColor Green
    Write-Host "   • Fallidas: $($sendResponse.failed)" -ForegroundColor $(if ($sendResponse.failed -gt 0) { "Red" } else { "Gray" })
    
    if ($sendResponse.errors.Count -gt 0) {
        Write-Host ""
        Write-Host "   ⚠️  Errores:" -ForegroundColor Yellow
        foreach ($error in $sendResponse.errors) {
            Write-Host "      - User $($error.user_id): $($error.error)" -ForegroundColor Red
        }
    }
    
    Write-Host ""
    Write-Host "🎯 VERIFICA TU DISPOSITIVO:" -ForegroundColor Cyan
    Write-Host "   • Si la app está abierta: Verás una notificación local" -ForegroundColor White
    Write-Host "   • Si la app está en background: Verás notificación del sistema" -ForegroundColor White
    Write-Host "   • Si la app está cerrada: Verás notificación del sistema" -ForegroundColor White
    Write-Host ""
    
} catch {
    Write-Host "   ❌ Error enviando notificación" -ForegroundColor Red
    
    if ($_.ErrorDetails.Message) {
        $errorDetail = $_.ErrorDetails.Message | ConvertFrom-Json
        Write-Host "   Detalles: $($errorDetail.error)" -ForegroundColor Red
    } else {
        Write-Host "   Detalles: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host ""
    Write-Host "💡 POSIBLES CAUSAS:" -ForegroundColor Yellow
    Write-Host "   1. El token FCM no está registrado correctamente" -ForegroundColor Gray
    Write-Host "   2. Firebase no está inicializado en el backend" -ForegroundColor Gray
    Write-Host "   3. El archivo de credenciales Firebase no está en la raíz" -ForegroundColor Gray
    Write-Host ""
    exit 1
}

Write-Host "=== PRUEBA COMPLETADA ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 TIPS:" -ForegroundColor Yellow
Write-Host "   • Puedes ejecutar este script múltiples veces" -ForegroundColor White
Write-Host "   • Cambia el título/mensaje editando el script" -ForegroundColor White
Write-Host "   • Verifica los logs del servidor Django para más detalles" -ForegroundColor White
Write-Host ""
