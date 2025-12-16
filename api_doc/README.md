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

6. **[04a1_citas_crud.md](04a1_citas_crud.md)** - Citas (CRUD Básico)
   - Crear cita
   - Ver mis citas
   - Ver detalle de cita
   - Actualizar cita
   - Eliminar cita

7. **[04a2_citas_acciones.md](04a2_citas_acciones.md)** - Citas (Acciones)
   - Confirmar cita
   - Cancelar cita
   - Marcar como completada
   - Próximas citas
   - Historial de citas

8. **[04b_citas_busqueda.md](04b_citas_busqueda.md)** - Citas (Búsqueda)
   - Horarios disponibles
   - Derivaciones
   - Citas con planes

9. **[05a1_historia_notas.md](05a1_historia_notas.md)** - Historia Clínica (Notas)
   - CRUD de notas de sesión

10. **[05a2_part1_historia_endpoints.md](05a2_part1_historia_endpoints.md)** - Historia Clínica (Endpoints)
    - Historial del paciente
    - Detalles específicos

11. **[05a2_part2_historia_referencia.md](05a2_part2_historia_referencia.md)** - Historia Clínica (Referencia)
    - Modelos y serializers

12. **[05b_historia_documentos.md](05b_historia_documentos.md)** - Historia Clínica (Documentos)
    - CRUD de documentos clínicos

13. **[06a_mood_journal.md](06a_mood_journal.md)** - Registro de Estado de Ánimo
    - Crear registro
    - Historial
    - Estadísticas

14. **[06b_objectives_tasks.md](06b_objectives_tasks.md)** - Objetivos y Tareas
    - CRUD de objetivos
    - CRUD de tareas

15. **[06c_triage.md](06c_triage.md)** - Triaje Inicial
    - Crear triaje
    - Ver triaje del paciente

16. **[07a_pagos_citas.md](07a_pagos_citas.md)** - Pagos (Citas Individuales)
    - Crear sesión de pago
    - Confirmar pago
    - Ver estado de pago
    - Historial de pagos
    - Clave pública de Stripe

17. **[07b_pagos_planes.md](07b_pagos_planes.md)** - Pagos (Planes de Sesiones)
    - Listar planes disponibles
    - Comprar plan
    - Mis planes comprados

18. **[07c_pagos_webhook.md](07c_pagos_webhook.md)** - Pagos (Webhook)
    - Procesamiento automático de pagos (técnico)

19. **[08a_admin_usuarios.md](08a_admin_usuarios.md)** - Administración (Gestión de Usuarios)
    - Listar usuarios
    - Ver/actualizar/desactivar usuarios
    - Ver documentos de verificación
    - Verificar perfil profesional

20. **[08b_admin_reportes.md](08b_admin_reportes.md)** - Administración (Reportes)
    - Ver reporte de pagos (con filtros)
    - Descargar reporte CSV
    - Descargar reporte PDF

21. **[09_chat.md](09_chat.md)** - Chat de Citas
    - Listar mensajes de cita
    - Enviar mensaje en chat

22. **[10_backups.md](10_backups.md)** - Sistema de Backups
    - Crear backup (SQL/JSON) y subir a S3
    - Restaurar backup desde archivo
    - Listar backups en S3
    - Descargar backup desde S3
    - Eliminar backup de S3
    - Obtener URL de descarga prefirmada

23. **[11_auditlog.md](11_auditlog.md)** - Bitácora de Auditoría
    - Listar registros de auditoría (con filtros)
    - Ver detalle de registro
    - Exportar bitácora a PDF

24. **[12a_tenants_public.md](12a_tenants_public.md)** - Tenants (Endpoints Públicos)
    - Listar clínicas públicas
    - Registrar nueva clínica (auto-onboarding)
    - Verificar disponibilidad de subdominio

25. **[12b_tenants_admin.md](12b_tenants_admin.md)** - Tenants (Endpoints Administrativos)
    - CRUD de clínicas (admin)
    - Estadísticas globales (todas las clínicas)
    - Estadísticas por clínica específica

26. **[00_general.md](00_general.md)** - Información General
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
