# Script para enviar notificación push de prueba a Ana Torres
# Fecha: 2025-11-24

Write-Host "=== TEST DE NOTIFICACIONES PUSH - ANA TORRES ===" -ForegroundColor Cyan
Write-Host ""

# Configuración
$baseUrl = "https://api.psicoadmin.xyz"
$tenantSchema = "bienestar"

# Credenciales de Ana Torres
$email = "ana.torres@example.com"
$password = "password123"  # Ajusta si es diferente

Write-Host "📝 Paso 1: Login como Ana Torres..." -ForegroundColor Yellow
Write-Host "   Email: $email" -ForegroundColor Gray

try {
    $loginResponse = Invoke-RestMethod -Uri "$baseUrl/api/auth/login/" `
        -Method POST `
        -Headers @{
            "Content-Type" = "application/json"
            "X-Tenant-Schema" = $tenantSchema
        } `
        -Body (@{
            email = $email
            password = $password
        } | ConvertTo-Json)

    $token = $loginResponse.access
    $userId = $loginResponse.user.id
    $userName = $loginResponse.user.full_name

    Write-Host "   ✅ Login exitoso" -ForegroundColor Green
    Write-Host "   👤 Usuario: $userName (ID: $userId)" -ForegroundColor Gray
    Write-Host "   🔑 Token obtenido" -ForegroundColor Gray
    Write-Host ""

} catch {
    Write-Host "   ❌ Error en login: $_" -ForegroundColor Red
    Write-Host "   💡 Verifica que la contraseña sea correcta" -ForegroundColor Yellow
    exit 1
}

Write-Host "📝 Paso 2: Verificar endpoint de notificaciones..." -ForegroundColor Yellow

try {
    $vapidResponse = Invoke-RestMethod -Uri "$baseUrl/api/notifications/vapid-public-key/" `
        -Headers @{"X-Tenant-Schema" = $tenantSchema}
    
    Write-Host "   ✅ VAPID Public Key disponible" -ForegroundColor Green
    Write-Host "   🔑 Key: $($vapidResponse.public_key.Substring(0,20))..." -ForegroundColor Gray
    Write-Host ""

} catch {
    Write-Host "   ❌ Error verificando VAPID: $_" -ForegroundColor Red
    exit 1
}

Write-Host "📝 Paso 3: Enviar notificación de prueba..." -ForegroundColor Yellow

try {
    $notificationPayload = @{
        user_id = $userId
        title = "🎉 ¡Hola Ana!"
        message = "Esta es tu primera notificación push. El sistema está funcionando correctamente."
        url = "/dashboard"
    }

    Write-Host "   📤 Enviando notificación..." -ForegroundColor Gray
    Write-Host "   📋 Título: $($notificationPayload.title)" -ForegroundColor Gray
    Write-Host "   💬 Mensaje: $($notificationPayload.message)" -ForegroundColor Gray

    $sendResponse = Invoke-RestMethod -Uri "$baseUrl/api/notifications/send/" `
        -Method POST `
        -Headers @{
            "Content-Type" = "application/json"
            "Authorization" = "Bearer $token"
            "X-Tenant-Schema" = $tenantSchema
        } `
        -Body ($notificationPayload | ConvertTo-Json)

    Write-Host ""
    Write-Host "   ✅ NOTIFICACIÓN ENVIADA EXITOSAMENTE" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Resultado del envío:" -ForegroundColor Cyan
    Write-Host "   • Total enviadas: $($sendResponse.sent_count)" -ForegroundColor Gray
    Write-Host "   • Total fallidas: $($sendResponse.failed_count)" -ForegroundColor Gray
    
    if ($sendResponse.sent_count -gt 0) {
        Write-Host ""
        Write-Host "🎯 Detalles de suscripciones:" -ForegroundColor Cyan
        foreach ($detail in $sendResponse.details) {
            if ($detail.success) {
                Write-Host "   ✓ Suscripción ID: $($detail.subscription_id) - Enviada" -ForegroundColor Green
            } else {
                Write-Host "   ✗ Suscripción ID: $($detail.subscription_id) - Error: $($detail.error)" -ForegroundColor Red
            }
        }
    }

    Write-Host ""
    Write-Host "=== INSTRUCCIONES PARA VER LA NOTIFICACIÓN ===" -ForegroundColor Yellow
    Write-Host "1. Asegúrate de haber instalado la PWA desde el navegador" -ForegroundColor White
    Write-Host "2. Abre la PWA instalada (no el navegador)" -ForegroundColor White
    Write-Host "3. Ve a tu Perfil y activa las notificaciones" -ForegroundColor White
    Write-Host "4. Ejecuta este script nuevamente para enviar otra notificación" -ForegroundColor White
    Write-Host "5. Deberías ver la notificación aparecer en tu sistema" -ForegroundColor White
    Write-Host ""

    if ($sendResponse.sent_count -eq 0) {
        Write-Host "⚠️  NO HAY SUSCRIPCIONES ACTIVAS" -ForegroundColor Yellow
        Write-Host "   Ana Torres aún no ha activado las notificaciones en la PWA" -ForegroundColor Gray
        Write-Host "   Debe:" -ForegroundColor Gray
        Write-Host "   1. Instalar la PWA desde https://bienestar.psicoadmin.xyz/" -ForegroundColor Gray
        Write-Host "   2. Abrir la PWA instalada" -ForegroundColor Gray
        Write-Host "   3. Ir a Perfil > Notificaciones" -ForegroundColor Gray
        Write-Host "   4. Hacer clic en 'Activar notificaciones'" -ForegroundColor Gray
        Write-Host "   5. Conceder permisos cuando el navegador lo solicite" -ForegroundColor Gray
        Write-Host ""
    }

} catch {
    Write-Host "   ❌ Error enviando notificación: $_" -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "   Detalles: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
    exit 1
}

Write-Host "=== SCRIPT COMPLETADO ===" -ForegroundColor Cyan
Write-Host ""
