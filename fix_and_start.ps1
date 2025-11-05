# Script para arreglar dependencias e iniciar el servidor
Write-Host "=== Arreglando Dependencias e Iniciando Servidor ===" -ForegroundColor Cyan

# 1. Detener todos los procesos Python
Write-Host "`n1. Deteniendo procesos Python existentes..." -ForegroundColor Yellow
Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# 2. Instalar supabase
Write-Host "`n2. Instalando supabase..." -ForegroundColor Yellow
pip install supabase

# 3. Verificar instalacion
Write-Host "`n3. Verificando instalacion de supabase..." -ForegroundColor Yellow
python -c "import supabase; print('supabase instalado correctamente')"

# 4. Iniciar servidor
Write-Host "`n4. Iniciando servidor Django..." -ForegroundColor Yellow
Write-Host "Presiona Ctrl+C para detener el servidor" -ForegroundColor Gray
python manage.py runserver
