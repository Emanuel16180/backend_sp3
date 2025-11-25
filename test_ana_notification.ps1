Write-Host "=== TEST NOTIFICACIONES - ANA TORRES ===" -ForegroundColor Cyan

$baseUrl = "https://api.psicoadmin.xyz"
$tenantSchema = "bienestar"
$email = "ana.torres@example.com"
$password = "password123"

Write-Host "Login..." -ForegroundColor Yellow

$loginResponse = Invoke-RestMethod -Uri "$baseUrl/api/auth/login/" -Method POST -Headers @{"Content-Type" = "application/json"; "X-Tenant-Schema" = $tenantSchema} -Body (@{email = $email; password = $password} | ConvertTo-Json)

$token = $loginResponse.access
$userId = $loginResponse.user.id

Write-Host "Login exitoso - Usuario ID: $userId" -ForegroundColor Green

Write-Host "Enviando notificacion..." -ForegroundColor Yellow

$notification = @{user_id = $userId; title = "Hola Ana"; message = "Notificacion de prueba"; url = "/dashboard"}

$result = Invoke-RestMethod -Uri "$baseUrl/api/notifications/send/" -Method POST -Headers @{"Content-Type" = "application/json"; "Authorization" = "Bearer $token"; "X-Tenant-Schema" = $tenantSchema} -Body ($notification | ConvertTo-Json)

Write-Host "Enviadas: $($result.sent_count) | Fallidas: $($result.failed_count)" -ForegroundColor Green

if ($result.sent_count -eq 0) {
    Write-Host "Ana debe activar notificaciones en la PWA instalada" -ForegroundColor Yellow
}
