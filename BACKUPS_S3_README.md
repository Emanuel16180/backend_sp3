# 📦 Sistema de Backups en AWS S3

## ✅ Configuración Completa

El sistema de backups en la nube ya está configurado y funcionando correctamente.

### 🔐 Credenciales Configuradas
- **Bucket S3**: `psico-backups-2025`
- **Región**: `us-east-1` (Virginia del Norte)
- **Usuario IAM**: `psico-backup-admin`
- **Credenciales**: Configuradas en `.env`

---

## 📚 Endpoints Disponibles

### 1. **Crear Backup y Subir a S3**
```http
POST /api/backups/create/
Authorization: Token <tu_token>
```

**Query Parameters:**
- `cloud_only=true` - Solo sube a S3, no descarga localmente
- `download=true` - Descarga el backup localmente y también sube a S3

**Respuesta (cloud_only=true):**
```json
{
  "message": "Backup creado y subido a S3 exitosamente",
  "backup_info": {
    "filename": "backup-sql-bienestar-2025-10-20-162000.sql",
    "s3_key": "backups/bienestar/backup-sql-bienestar-2025-10-20-162000.sql",
    "size": 123456,
    "bucket": "psico-backups-2025",
    "url": "https://psico-backups-2025.s3.us-east-1.amazonaws.com/..."
  }
}
```

---

### 2. **Listar Backups en S3**
```http
GET /api/backups/cloud/list/
Authorization: Token <tu_token>
```

**Respuesta:**
```json
{
  "count": 5,
  "schema": "bienestar",
  "backups": [
    {
      "filename": "backup-sql-bienestar-2025-10-20-162000.sql",
      "s3_key": "backups/bienestar/backup-sql-bienestar-2025-10-20-162000.sql",
      "size": 123456,
      "last_modified": "2025-10-20T16:20:00.000Z",
      "storage_class": "STANDARD",
      "url": "https://psico-backups-2025.s3.us-east-1.amazonaws.com/..."
    }
  ]
}
```

---

### 3. **Descargar Backup desde S3**
```http
POST /api/backups/cloud/download/
Authorization: Token <tu_token>
Content-Type: application/json

{
  "s3_key": "backups/bienestar/backup-sql-bienestar-2025-10-20-162000.sql"
}
```

**Respuesta:** Archivo descargado directamente

---

### 4. **Eliminar Backup de S3**
```http
DELETE /api/backups/cloud/delete/
Authorization: Token <tu_token>
Content-Type: application/json

{
  "s3_key": "backups/bienestar/backup-sql-bienestar-2025-10-20-162000.sql"
}
```

**Respuesta:**
```json
{
  "message": "Backup eliminado exitosamente de S3",
  "s3_key": "backups/bienestar/backup-sql-bienestar-2025-10-20-162000.sql"
}
```

---

### 5. **Obtener URL de Descarga Prefirmada**
```http
POST /api/backups/cloud/get-url/
Authorization: Token <tu_token>
Content-Type: application/json

{
  "s3_key": "backups/bienestar/backup-sql-bienestar-2025-10-20-162000.sql",
  "expiration": 3600  // opcional, por defecto 3600 segundos (1 hora)
}
```

**Respuesta:**
```json
{
  "download_url": "https://psico-backups-2025.s3.amazonaws.com/...",
  "s3_key": "backups/bienestar/backup-sql-bienestar-2025-10-20-162000.sql",
  "expires_in_seconds": 3600,
  "filename": "backup-sql-bienestar-2025-10-20-162000.sql"
}
```

---

## 🔒 Seguridad

### Permisos
- Solo los administradores de cada clínica pueden crear, ver y descargar backups
- Los backups están organizados por schema (clínica)
- No se puede acceder a backups de otras clínicas

### Encriptación
- Los archivos se almacenan con encriptación AES-256 en el servidor de AWS
- Las credenciales están en variables de entorno (`.env`)
- URLs prefirmadas con expiración temporal

---

## 💾 Estructura en S3

```
psico-backups-2025/
├── backups/
│   ├── bienestar/
│   │   ├── backup-sql-bienestar-2025-10-20-100000.sql
│   │   ├── backup-sql-bienestar-2025-10-20-120000.sql
│   │   └── ...
│   ├── mindcare/
│   │   ├── backup-sql-mindcare-2025-10-20-100000.sql
│   │   └── ...
│   └── ...
└── test/
    └── (archivos de prueba)
```

---

## 🧪 Prueba del Sistema

Para verificar que todo funciona:

```bash
python test_s3_backup.py
```

---

## 📊 Ventajas del Sistema

✅ **Backups automáticos en la nube** - No depende del servidor local
✅ **Alta disponibilidad** - AWS S3 tiene 99.999999999% de durabilidad
✅ **Seguridad** - Encriptación AES-256 y control de acceso
✅ **Escalable** - Ilimitado espacio de almacenamiento
✅ **Económico** - Solo pagas por lo que usas (~$0.023/GB/mes)
✅ **Versionado** - Cada backup tiene timestamp único
✅ **Recuperación rápida** - Descarga desde cualquier lugar

---

## 🚀 Uso en Producción

1. **Configurar backups automáticos** (recomendado):
   - Crear un cron job o tarea programada
   - Ejecutar backup diario de cada clínica
   
2. **Política de retención**:
   - Mantener backups diarios de la última semana
   - Backups semanales del último mes
   - Backups mensuales del último año

3. **Monitoreo**:
   - Revisar logs de auditoría en `/api/auditlog/`
   - Verificar tamaño de bucket regularmente
   - Configurar alertas de AWS CloudWatch

---

## 📝 Variables de Entorno

Asegúrate de tener configurado en `.env`:

```env
# AWS S3 Configuration
AWS_ACCESS_KEY_ID="tu_aws_access_key_aqui"
AWS_SECRET_ACCESS_KEY="tu_aws_secret_key_aqui"
AWS_STORAGE_BUCKET_NAME="psico-backups-2025"
AWS_S3_REGION_NAME="us-east-1"
```

---

## ⚠️ IMPORTANTE

- **NUNCA** commitees el archivo `.env` al repositorio
- Mantén tus credenciales de AWS seguras
- Rota las credenciales cada 90 días
- Configura MFA en la cuenta de AWS
- Revisa regularmente los costos en AWS

---

## 💰 Costos Estimados

Para una clínica con:
- 10 backups por mes (1 GB cada uno)
- Total: 10 GB almacenados

**Costo mensual**: ~$0.23 USD

AWS S3 ofrece 5 GB gratis el primer año en el tier gratuito.

---

¿Necesitas ayuda? Revisa los logs en la base de datos o contacta al administrador del sistema.
