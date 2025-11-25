Write-Host "Esperando deploy de Render (120 segundos)..." -ForegroundColor Yellow
Start-Sleep -Seconds 120

Write-Host ""
Write-Host "Ejecutando test de notificaciones..." -ForegroundColor Cyan
.\test_notification_ana.ps1
