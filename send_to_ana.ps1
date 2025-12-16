Write-Host "=== ENVIO NOTIFICACION A ANA TORRES ===" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "https://api.psicoadmin.xyz"
$tenantSchema = "bienestar"

Write-Host "1. Login Dr. Valverde..." -ForegroundColor Yellow

$loginResp = Invoke-RestMethod -Uri "$baseUrl/api/auth/login/" -Method POST -Headers @{"Content-Type" = "application/json"; "X-Tenant-Schema" = $tenantSchema} -Body (@{email = "dr.valverde@bienestar.com"; password = "demo123"} | ConvertTo-Json)

$token = $loginResp.token
Write-Host "   OK - Token: $($token.Substring(0,10))..." -ForegroundColor Green
Write-Host ""

Write-Host "2. Enviando notificacion..." -ForegroundColor Yellow

$notification = @{user_id = 46; title = "Hola Ana!"; body = "Notificacion de prueba"; url = "/dashboard"}

try {
    $result = Invoke-RestMethod -Uri "$baseUrl/api/notifications/send/" -Method POST -Headers @{"Content-Type" = "application/json"; "Authorization" = "Token $token"; "X-Tenant-Schema" = $tenantSchema} -Body ($notification | ConvertTo-Json)

    Write-Host "   OK" -ForegroundColor Green
    Write-Host ""
    Write-Host "RESULTADO:" -ForegroundColor Cyan
    Write-Host "Total: $($result.total) | Enviadas: $($result.sent) | Fallidas: $($result.failed)" -ForegroundColor White

    if ($result.sent -eq 0) {
        Write-Host ""
        Write-Host "Ana debe activar notificaciones:" -ForegroundColor Yellow
        Write-Host "1. Instalar PWA: https://bienestar.psicoadmin.xyz/" -ForegroundColor Gray
        Write-Host "2. Login: ana.torres@example.com / demo123" -ForegroundColor Gray
        Write-Host "3. Perfil -> Notificaciones -> Activar" -ForegroundColor Gray
    }
} catch {
    Write-Host "   ERROR: $($_.Exception.Message)" -ForegroundColor Red
}
