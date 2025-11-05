# 🧪 PRUEBAS HTTP DEL SISTEMA

Esta carpeta contiene archivos `.http` para probar todos los flujos del sistema.

## 📁 Estructura de Archivos

### Autenticación
- `01_auth_registro.http` - Registro de nuevos usuarios
- `02_auth_login.http` - Login de usuarios
- `03_auth_recuperar_password.http` - Recuperación de contraseña

### Pacientes
- `10_paciente_perfil.http` - Gestión de perfil del paciente
- `11_paciente_triaje.http` - Triaje inicial
- `12_paciente_buscar_profesionales.http` - Búsqueda de profesionales
- `13_paciente_agendar_cita.http` - Agendamiento de citas
- `14_paciente_mood_journal.http` - Diario de estado de ánimo
- `15_paciente_objetivos_tareas.http` - Objetivos y tareas

### Profesionales
- `20_profesional_perfil.http` - Completar perfil profesional
- `21_profesional_disponibilidad.http` - Configurar horarios
- `22_profesional_citas.http` - Gestionar citas
- `23_profesional_historia_clinica.http` - Historias clínicas
- `24_profesional_planes_cuidado.http` - Planes de cuidado

### Administradores
- `30_admin_usuarios.http` - Gestión de usuarios
- `31_admin_verificacion.http` - Verificación de profesionales
- `32_admin_reportes.http` - Reportes y estadísticas

### Pagos
- `40_pagos_stripe.http` - Sistema de pagos

## 🎯 Variables de Entorno

Cada archivo usa variables que debes configurar:

### VS Code REST Client
Crea un archivo `.vscode/settings.json` con:

```json
{
  "rest-client.environmentVariables": {
    "$shared": {
      "baseUrl": "http://bienestar.localhost:8000",
      "baseMindcare": "http://mindcare.localhost:8000"
    },
    "bienestar": {
      "baseUrl": "http://bienestar.localhost:8000"
    },
    "mindcare": {
      "baseUrl": "http://mindcare.localhost:8000"
    }
  }
}
```

## 🔑 Credenciales de Prueba

### Clínica Bienestar

**Admin:**
- Email: `admin@bienestar.com`
- Password: `admin123`

**Profesionales:**
- `dra.martinez@bienestar.com` / `demo123`
- `dr.garcia@bienestar.com` / `demo123`

**Pacientes:**
- `juan.perez@example.com` / `demo123`
- `maria.gomez@example.com` / `demo123`

### Clínica Mindcare

**Admin:**
- Email: `admin@mindcare.com`
- Password: `admin123`

**Profesionales:**
- `dra.torres@mindcare.com` / `demo123`

**Pacientes:**
- `carlos.ruiz@example.com` / `demo123`

## 📝 Cómo Usar

1. Instala la extensión "REST Client" en VS Code
2. Abre cualquier archivo `.http`
3. Click en "Send Request" sobre cada petición
4. Las variables se guardan automáticamente entre peticiones

## ⚠️ Orden Recomendado

1. Primero ejecuta `02_auth_login.http` para obtener el token
2. El token se guarda automáticamente en `@authToken`
3. Luego puedes ejecutar los demás archivos en orden
