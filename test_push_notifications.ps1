# TEST PUSH NOTIFICATIONS - PowerShell Script
# Asegúrate de tener un token válido de autenticación

# 1. OBTENER CLAVE PÚBLICA VAPID
Write-Host "🔑 Obteniendo clave pública VAPID..." -ForegroundColor Cyan
$vapidResponse = Invoke-RestMethod -Uri "https://api.psicoadmin.xyz/api/notifications/vapid-public-key/" `
    -Method GET `
    -Headers @{
        "X-Tenant-Schema" = "bienestar"
    }
Write-Host "✅ Clave pública VAPID:" -ForegroundColor Green
Write-Host $vapidResponse.public_key
Write-Host ""

# 2. SUSCRIBIR DISPOSITIVO (requiere autenticación)
# Primero, obtén un token de autenticación
Write-Host "🔐 Iniciando sesión..." -ForegroundColor Cyan
$loginResponse = Invoke-RestMethod -Uri "https://api.psicoadmin.xyz/api/auth/login/" `
    -Method POST `
    -Headers @{
        "Content-Type" = "application/json"
        "X-Tenant-Schema" = "bienestar"
    } `
    -Body '{"email": "admin@bienestar.com", "password": "admin123"}'

$token = $loginResponse.token
Write-Host "✅ Token obtenido: $token" -ForegroundColor Green
Write-Host ""

# 3. REGISTRAR SUSCRIPCIÓN (simulada con datos de prueba)
Write-Host "📱 Registrando suscripción de prueba..." -ForegroundColor Cyan
$subscriptionData = @{
    endpoint = "https://fcm.googleapis.com/fcm/send/test-endpoint-12345"
    keys = @{
        p256dh = "BNVdhBTDqH9WQRtYuLqy1VjA7QSEZPwlM0vgxmVn4K3a6to8unUoie_ZaqA8TzXAg49ExZ8PXqccm63T0tmq_j0"
        auth = "abcd1234efgh5678ijkl9012"
    }
} | ConvertTo-Json

$subscribeResponse = Invoke-RestMethod -Uri "https://api.psicoadmin.xyz/api/notifications/subscribe/" `
    -Method POST `
    -Headers @{
        "Content-Type" = "application/json"
        "Authorization" = "Token $token"
        "X-Tenant-Schema" = "bienestar"
    } `
    -Body $subscriptionData

Write-Host "✅ Suscripción registrada:" -ForegroundColor Green
Write-Host ($subscribeResponse | ConvertTo-Json)
Write-Host ""

# 4. ENVIAR NOTIFICACIÓN (solo admins)
Write-Host "🔔 Enviando notificación de prueba..." -ForegroundColor Cyan
$notificationData = @{
    user_id = $loginResponse.user.id
    title = "Prueba de Notificación"
    body = "Esta es una notificación de prueba desde PowerShell"
    url = "https://bienestar.psicoadmin.xyz/"
} | ConvertTo-Json

try {
    $sendResponse = Invoke-RestMethod -Uri "https://api.psicoadmin.xyz/api/notifications/send/" `
        -Method POST `
        -Headers @{
            "Content-Type" = "application/json"
            "Authorization" = "Token $token"
            "X-Tenant-Schema" = "bienestar"
        } `
        -Body $notificationData
    
    Write-Host "✅ Notificación enviada:" -ForegroundColor Green
    Write-Host ($sendResponse | ConvertTo-Json)
} catch {
    Write-Host "⚠️ Error enviando notificación (puede ser que el usuario no sea admin):" -ForegroundColor Yellow
    Write-Host $_.Exception.Message
}
Write-Host ""

# 5. VER HISTORIAL DE NOTIFICACIONES
Write-Host "📜 Obteniendo historial de notificaciones..." -ForegroundColor Cyan
$historyResponse = Invoke-RestMethod -Uri "https://api.psicoadmin.xyz/api/notifications/history/" `
    -Method GET `
    -Headers @{
        "Authorization" = "Token $token"
        "X-Tenant-Schema" = "bienestar"
    }

Write-Host "✅ Historial de notificaciones:" -ForegroundColor Green
Write-Host ($historyResponse | ConvertTo-Json -Depth 5)
