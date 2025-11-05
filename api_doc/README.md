# 📚 API DOCUMENTATION - BIENESTAR MENTAL

**Versión:** 1.0  
**Fecha:** 5 de Noviembre 2025  
**Base URL:** `http://localhost:8000`

---

## 📁 ESTRUCTURA DE LA DOCUMENTACIÓN

Esta documentación está dividida en archivos separados para facilitar su lectura y mantenimiento:

### Archivos Disponibles

1. **[01_authentication.md](01_authentication.md)** - Autenticación y Autorización
   - Registro de usuarios
   - Login/Logout
   - Cambio de contraseña
   - Perfil de usuario

2. **[02a_users_consultas.md](02a_users_consultas.md)** - Gestión de Usuarios (Consultas)
   - Ver perfil de usuario
   - Ver perfil de paciente

3. **[02b_users_modificaciones.md](02b_users_modificaciones.md)** - Gestión de Usuarios (Modificaciones)
   - Crear perfil de paciente
   - Actualizar perfil de paciente (PUT/PATCH)
   - Actualizar perfil completo (usuario + paciente)
   - Eliminación de cuenta

4. **[03a_professionals_consultas.md](03a_professionals_consultas.md)** - Profesionales (Consultas)
   - Listar profesionales (búsqueda)
   - Ver perfil público
   - Ver propio perfil
   - Especialidades
   - Reseñas de profesional
   - Listar colegas

5. **[03b_professionals_modificaciones.md](03b_professionals_modificaciones.md)** - Profesionales (Modificaciones)
   - Crear perfil profesional
   - Actualizar perfil (PUT/PATCH)
   - Crear reseña
   - Planes de cuidado (CRUD)
   - Subir documentos de verificación

6. **[04_appointments.md](04_appointments.md)** - Citas
   - CRUD de citas
   - Confirmación, cancelación, completar
   - Próximas citas e historial
   - Búsqueda de disponibilidad
   - Derivaciones

7. **[05_clinical_history.md](05_clinical_history.md)** - Historia Clínica
   - Notas de sesión
   - Documentos clínicos
   - Historial del paciente

8. **[06_mood_goals_triage.md](06_mood_goals_triage.md)** - Bienestar del Paciente
   - Registro de estado de ánimo
   - Objetivos y tareas
   - Triaje inicial

8. **[00_general.md](00_general.md)** - Información General
   - Autenticación con tokens
   - Códigos de error comunes
   - Convenciones de la API

---

## 🔑 AUTENTICACIÓN

Todos los endpoints protegidos requieren un token de autenticación en el header:

```
Authorization: Token <tu_token_aqui>
```

Para obtener un token, usa el endpoint `/api/auth/login/`

---

## 🌐 MULTI-TENANCY

Esta API utiliza un sistema multi-tenant basado en subdominios:

- **Tenant público:** `public.localhost:8000` - Acceso general
- **Tenants privados:** `{tenant-slug}.localhost:8000` - Clínicas específicas

---

## 📝 CONVENCIONES

### Formatos de Fecha y Hora
- **Fecha:** `YYYY-MM-DD` (ejemplo: `2025-11-05`)
- **Hora:** `HH:MM:SS` (ejemplo: `14:30:00`)
- **DateTime:** ISO 8601 (ejemplo: `2025-11-05T14:30:00Z`)

### Códigos de Estado HTTP
- `200 OK` - Solicitud exitosa
- `201 Created` - Recurso creado
- `400 Bad Request` - Error de validación
- `401 Unauthorized` - No autenticado
- `403 Forbidden` - Sin permisos
- `404 Not Found` - Recurso no encontrado
- `500 Internal Server Error` - Error del servidor

---

## 🚀 INICIO RÁPIDO

1. **Registrar usuario:** `POST /api/auth/register/`
2. **Iniciar sesión:** `POST /api/auth/login/`
3. **Obtener perfil:** `GET /api/users/profile/`
4. **Buscar profesionales:** `GET /api/professionals/`
5. **Crear cita:** `POST /api/appointments/appointments/`

---

**Nota:** Cada archivo de documentación contiene información verificada directamente del código fuente (models.py, serializers.py, views.py).
