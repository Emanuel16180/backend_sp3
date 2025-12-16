# 🚀 GUÍA DE DESPLIEGUE EN RENDER (100% GRATIS)

## ⏱️ Tiempo Total: 10 minutos

---

## 📋 PASO 1: Subir Código a GitHub (5 minutos)

### 1.1 Crear repositorio en GitHub
1. Ve a https://github.com/new
2. Nombre: `psico-admin-multitenant`
3. **IMPORTANTE**: Marca como **Privado** (para proteger tus keys)
4. NO marques ninguna opción de README, .gitignore, etc.
5. Click en "Create repository"

### 1.2 Subir tu proyecto
```powershell
# En tu terminal de PowerShell (en la carpeta del proyecto):
cd "c:\Users\asus\Documents\SISTEMAS DE INFORMACION 2\2do Sprindt\psico_admin_sp1_despliegue2"

# Inicializar git (si no está ya)
git init

# Agregar todos los archivos
git add .

# Hacer commit
git commit -m "Configuración inicial para Render"

# Conectar con GitHub (reemplaza TU_USUARIO con tu usuario de GitHub)
git remote add origin https://github.com/TU_USUARIO/psico-admin-multitenant.git

# Subir código
git branch -M main
git push -u origin main
```

---

## 🎯 PASO 2: Desplegar en Render (5 minutos)

### 2.1 Crear cuenta en Render
1. Ve a https://render.com/
2. Click en "Get Started"
3. Registrarte con tu cuenta de GitHub (más fácil)

### 2.2 Conectar repositorio
1. En el dashboard de Render, click en "New +"
2. Selecciona "Blueprint"
3. Click en "Connect a repository"
4. Busca `psico-admin-multitenant` y click "Connect"

### 2.3 Configurar Variables de Entorno
Render detectará automáticamente el `render.yaml`, pero necesitas agregar estas variables sensibles:

En el dashboard de Render:
1. Ve a tu servicio `psico-admin`
2. Click en "Environment"
3. Agregar estas variables:

```
RENDER=True
AWS_ACCESS_KEY_ID=tu_aws_access_key_aqui
AWS_SECRET_ACCESS_KEY=tu_aws_secret_key_aqui
STRIPE_PUBLIC_KEY=tu_stripe_public_key_aqui
STRIPE_SECRET_KEY=tu_stripe_secret_key_aqui
STRIPE_WEBHOOK_SECRET=(si tienes uno)
```

**💡 IMPORTANTE**: Usa tus claves reales del archivo `.env` local (NO las subas a GitHub)

### 2.4 Desplegar
1. Click en "Apply"
2. Render automáticamente:
   - Creará la base de datos PostgreSQL
   - Instalará dependencias
   - Ejecutará migraciones
   - Desplegará la aplicación

---

## ✅ PASO 3: Crear Clínicas (2 minutos)

Una vez que el deploy termine:

### 3.1 Obtener URL de tu aplicación
En Render verás algo como: `https://psico-admin.onrender.com`

### 3.2 Crear clínicas via Shell
1. En Render, ve a tu servicio `psico-admin`
2. Click en "Shell" (arriba a la derecha)
3. Ejecuta:

```bash
python manage.py shell
```

```python
from apps.tenants.models import Clinic, Domain

# Crear clínica Bienestar
bienestar = Clinic.objects.create(
    schema_name='bienestar',
    name='Clínica Bienestar',
    paid_until='2026-12-31',
    on_trial=False
)
Domain.objects.create(
    domain='bienestar.psico-admin.onrender.com',
    tenant=bienestar,
    is_primary=True
)

# Crear clínica Mindcare
mindcare = Clinic.objects.create(
    schema_name='mindcare',
    name='Clínica Mindcare',
    paid_until='2026-12-31',
    on_trial=False
)
Domain.objects.create(
    domain='mindcare.psico-admin.onrender.com',
    tenant=mindcare,
    is_primary=True
)

print("✅ Clínicas creadas!")
exit()
```

### 3.3 Aplicar migraciones a las clínicas
```bash
python manage.py migrate_schemas
```

---

## 🌐 PASO 4: Acceder a tu Aplicación

Tu app estará disponible en:
- **Clínica Bienestar**: https://bienestar.psico-admin.onrender.com
- **Clínica Mindcare**: https://mindcare.psico-admin.onrender.com
- **Admin principal**: https://psico-admin.onrender.com/admin

---

## ⚠️ LIMITACIONES DEL PLAN GRATUITO

### ⏱️ Sleep Mode
- La app se dormirá después de 15 minutos sin uso
- Primera visita después del sleep: 30-60 segundos para despertar

### 🗄️ Base de Datos
- **IMPORTANTE**: Se borrará automáticamente después de 90 días
- Recibirás emails de Render antes de que ocurra
- Haz backups regulares con el sistema S3 que ya tienes configurado

### 💾 Storage
- Sin disco persistente en plan gratuito
- Los archivos subidos (media/) se perderán al reiniciar
- Los backups de base de datos están en S3 (seguros)

---

## 🔄 CÓMO HACER BACKUPS (antes de los 90 días)

### Backup Manual desde Render Shell
```bash
# Conectar a Shell en Render
python manage.py shell
```

```python
from apps.backups.views import CreateBackupAndDownloadView
from django.test import RequestFactory

factory = RequestFactory()
request = factory.post('/api/backups/create/', {'cloud_only': True})
view = CreateBackupAndDownloadView.as_view()
response = view(request)
print(f"✅ Backup creado en S3: {response.status_code}")
```

### Restaurar después de los 90 días
1. Render creará nueva BD automáticamente
2. Ve a Shell y ejecuta:
```bash
# Listar backups disponibles en S3
python -c "from apps.backups.s3_storage import S3BackupStorage; s = S3BackupStorage(); print([f['Key'] for f in s.list_backups()])"

# Descargar último backup y restaurar
python manage.py shell
```

```python
from apps.backups.s3_storage import S3BackupStorage
import subprocess

s3 = S3BackupStorage()
backups = s3.list_backups()
last_backup = backups[-1]['Key']

# Descargar
backup_data = s3.download_backup(last_backup)
with open('/tmp/backup.sql', 'wb') as f:
    f.write(backup_data)

# Restaurar (necesitarás la DATABASE_URL de las variables de entorno)
import os
db_url = os.environ['DATABASE_URL']
# Parsear y ejecutar psql restore...
```

---

## 📊 RESUMEN DE COSTOS

| Servicio | Costo | Limitación |
|----------|-------|------------|
| Web Service | **$0** | Se duerme después 15 min |
| PostgreSQL | **$0** | Se borra cada 90 días |
| AWS S3 | **~$0.23/mes** | 10GB storage + requests |
| **TOTAL** | **~$0.23/mes** | Ideal para demos/testing |

---

## 🆘 TROUBLESHOOTING

### Error: "This site can't be reached"
- La app está dormida, espera 60 segundos
- Refresh la página

### Error: "Server Error (500)"
- Ve a Render Dashboard → Logs
- Busca el error específico
- Probablemente falta una variable de entorno

### Base de datos vacía después de despertar
- Esto NO debería pasar (excepto cada 90 días)
- Si pasa antes, contacta soporte de Render

---

## 🎉 ¡LISTO!

Tu aplicación multi-tenant está desplegada y funcionando **100% gratis** por 3 días (o más).

**Recuerda**: 
- Hacer backups a S3 regularmente (ya tienes el sistema configurado)
- Antes de los 90 días, exporta tus datos o migra a plan de pago ($7/mes)
