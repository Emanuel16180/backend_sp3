# Script para probar notificaciones push a Ana Torres
$baseUrl = "https://api.psicoadmin.xyz"
$tenant = "bienestar"

Write-Host "=== TEST DE NOTIFICACIONES PUSH ===" -ForegroundColor Cyan
Write-Host ""

# 1. LOGIN como Dr. Valverde
Write-Host "1. Iniciando sesion como Dr. Valverde..." -ForegroundColor Yellow
$loginBody = @{
    email = "dr.valverde@bienestar.com"
    password = "demo123"
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod `
        -Uri "$baseUrl/api/auth/login/" `
        -Method POST `
        -Headers @{
            "Content-Type" = "application/json"
            "X-Tenant-Schema" = $tenant
        } `
        -Body $loginBody
    
    $token = $loginResponse.token
    Write-Host "   Login exitoso!" -ForegroundColor Green
    Write-Host "   Token obtenido: $($token.Substring(0,20))..." -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "   ERROR en login: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 2. ENVIAR NOTIFICACIÓN
Write-Host "2. Enviando notificacion a Ana Torres (ID: 46)..." -ForegroundColor Yellow

$notificationBody = @{
    user_id = 46
    title = "Prueba desde PowerShell"
    body = "Esta es una notificacion de prueba para Ana Torres"
    url = "/dashboard"
} | ConvertTo-Json

try {
    $sendResponse = Invoke-RestMethod `
        -Uri "$baseUrl/api/notifications/send/" `
        -Method POST `
        -Headers @{
            "Content-Type" = "application/json"
            "Authorization" = "Token $token"
            "X-Tenant-Schema" = $tenant
        } `
        -Body $notificationBody
    
    Write-Host "   Notificacion enviada!" -ForegroundColor Green
    Write-Host "   Respuesta:" -ForegroundColor Gray
    $sendResponse | ConvertTo-Json -Depth 3 | Write-Host
    Write-Host ""
} catch {
    Write-Host "   ERROR al enviar notificacion: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = [System.IO.StreamReader]::new($_.Exception.Response.GetResponseStream())
        $errorBody = $reader.ReadToEnd()
        Write-Host "   Detalles: $errorBody" -ForegroundColor Red
    }
    exit 1
}

Write-Host "=== TEST COMPLETADO ===" -ForegroundColor Cyan
