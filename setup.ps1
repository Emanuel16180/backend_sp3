# ============================================================
# 🚀 SCRIPT DE CONFIGURACIÓN COMPLETA - WINDOWS POWERSHELL
# ============================================================
# 
# Este script ejecuta la configuración completa del sistema
# en un solo comando para Windows.
#
# USO:
#   .\setup.ps1
#
# ============================================================

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  🚀 CONFIGURACIÓN COMPLETA DEL SISTEMA" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Verificar que estamos en el directorio correcto
if (-not (Test-Path "manage.py")) {
    Write-Host "❌ Error: Este script debe ejecutarse desde el directorio raíz del proyecto" -ForegroundColor Red
    Write-Host "   (donde se encuentra manage.py)" -ForegroundColor Red
    exit 1
}

# Verificar entorno virtual
if ($env:VIRTUAL_ENV) {
    Write-Host "✅ Entorno virtual detectado: $env:VIRTUAL_ENV" -ForegroundColor Green
} else {
    Write-Host "⚠️  Advertencia: No se detectó un entorno virtual activo" -ForegroundColor Yellow
    Write-Host "   Recomendado: Activa tu entorno virtual primero" -ForegroundColor Yellow
    Write-Host "   Ejemplo: .\.venv\Scripts\Activate.ps1" -ForegroundColor Yellow
    Write-Host ""
    
    $response = Read-Host "¿Deseas continuar sin entorno virtual? (s/n)"
    if ($response -ne "s") {
        Write-Host "❌ Operación cancelada" -ForegroundColor Red
        exit 0
    }
}

Write-Host ""
Write-Host "Este script ejecutará los siguientes pasos:" -ForegroundColor White
Write-Host "  1️⃣  Crear tenant público" -ForegroundColor White
Write-Host "  2️⃣  Migrar base de datos" -ForegroundColor White
Write-Host "  3️⃣  Crear clínicas (bienestar y mindcare)" -ForegroundColor White
Write-Host "  4️⃣  Migrar schemas de clínicas" -ForegroundColor White
Write-Host "  5️⃣  Crear administradores" -ForegroundColor White
Write-Host "  6️⃣  Poblar datos de demostración" -ForegroundColor White
Write-Host ""

$confirm = Read-Host "¿Deseas continuar? (s/n)"
if ($confirm -ne "s") {
    Write-Host "❌ Operación cancelada" -ForegroundColor Red
    exit 0
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  🔧 INICIANDO CONFIGURACIÓN..." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Ejecutar el script de Python
python setup_complete.py

# Verificar resultado
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "  ✅ CONFIGURACIÓN COMPLETADA EXITOSAMENTE" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "🚀 PRÓXIMOS PASOS:" -ForegroundColor Cyan
    Write-Host "  1. Iniciar el servidor: python manage.py runserver" -ForegroundColor White
    Write-Host "  2. Acceder al admin: http://localhost:8000/admin/" -ForegroundColor White
    Write-Host "  3. Probar APIs con archivos .http en carpeta http_tests/" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host "  ❌ ERROR EN LA CONFIGURACIÓN" -ForegroundColor Red
    Write-Host "============================================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "⚠️  Revisa los mensajes de error anteriores" -ForegroundColor Yellow
    Write-Host "   Para más ayuda, consulta el README.md" -ForegroundColor Yellow
    Write-Host ""
    exit 1
}
