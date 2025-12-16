Write-Host "=== TEST NOTIFICACIONES - ANA TORRES ===" -ForegroundColor Cyan

$baseUrl = "https://api.psicoadmin.xyz"
$tenantSchema = "bienestar"
$email = "ana.torres@example.com"
$password = "demo123"

Write-Host "Login..." -ForegroundColor Yellow

$loginResponse = Invoke-RestMethod -Uri "$baseUrl/api/auth/login/" -Method POST -Headers @{"Content-Type" = "application/json"; "X-Tenant-Schema" = $tenantSchema} -Body (@{email = $email; password = $password} | ConvertTo-Json)

$token = $loginResponse.access
$userId = $loginResponse.user.id

Write-Host "Login exitoso - Usuario ID: $userId" -ForegroundColor Green

Write-Host "Enviando notificacion..." -ForegroundColor Yellow

$notification = @{user_id = $userId; title = "Hola Ana!"; message = "Esta es tu primera notificacion push desde PsicoAdmin"; url = "/dashboard"}

$result = Invoke-RestMethod -Uri "$baseUrl/api/notifications/send/" -Method POST -Headers @{"Content-Type" = "application/json"; "Authorization" = "Bearer $token"; "X-Tenant-Schema" = $tenantSchema} -Body ($notification | ConvertTo-Json)

Write-Host "Enviadas: $($result.sent_count) | Fallidas: $($result.failed_count)" -ForegroundColor Green

if ($result.sent_count -eq 0) {
    Write-Host ""
    Write-Host "NO HAY SUSCRIPCIONES ACTIVAS" -ForegroundColor Yellow
    Write-Host "Ana debe:" -ForegroundColor Gray
    Write-Host "1. Instalar la PWA desde https://bienestar.psicoadmin.xyz/" -ForegroundColor Gray
    Write-Host "2. Abrir la PWA instalada (no el navegador)" -ForegroundColor Gray
    Write-Host "3. Ir a Perfil - Notificaciones - Activar notificaciones" -ForegroundColor Gray
    Write-Host "4. Conceder permisos cuando el navegador lo solicite" -ForegroundColor Gray
} else {
    Write-Host "Notificacion enviada exitosamente!" -ForegroundColor Green
    Write-Host "Revisa la PWA instalada para ver la notificacion" -ForegroundColor Cyan
}
