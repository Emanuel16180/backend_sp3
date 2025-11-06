# 🔧 Configuración del Frontend para Multi-Tenant

## ⚠️ PROBLEMA ACTUAL

El frontend está haciendo peticiones a:
```
❌ https://bienestar.psicoadmin.xyz/api/auth/login/
```

Esto está **INCORRECTO** porque:
- `bienestar.psicoadmin.xyz` apunta a **Vercel** (frontend)
- El backend está en **Render** con dominio `api.psicoadmin.xyz`

## ✅ CONFIGURACIÓN CORRECTA

### 1. URL Base de la API

**Todas las peticiones** deben ir a:
```javascript
const API_BASE_URL = 'https://api.psicoadmin.xyz/api';
```

### 2. Header de Tenant Requerido

Cada petición debe incluir el header:
```javascript
{
  'X-Tenant-Schema': 'bienestar'  // o 'mindcare'
}
```

---

## 📝 Código de Ejemplo

### Opción 1: Configuración con Axios

```javascript
// src/config/api.js
import axios from 'axios';

// 🎯 URL FIJA - SIEMPRE apunta a Render
const API_BASE_URL = 'https://api.psicoadmin.xyz/api';

// 🏥 Detectar tenant desde el subdomain del frontend
const getTenantFromDomain = () => {
  const hostname = window.location.hostname;
  
  if (hostname.includes('bienestar')) {
    return 'bienestar';
  } else if (hostname.includes('mindcare')) {
    return 'mindcare';
  }
  
  return 'public'; // fallback
};

// Crear instancia de axios
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  }
});

// 🔥 INTERCEPTOR: Agregar header X-Tenant-Schema automáticamente
api.interceptors.request.use((config) => {
  const tenant = getTenantFromDomain();
  config.headers['X-Tenant-Schema'] = tenant;
  
  console.log('🎯 API Request:', {
    url: config.url,
    tenant: tenant,
    fullUrl: `${config.baseURL}${config.url}`
  });
  
  return config;
});

export default api;
```

### Opción 2: Función de Login

```javascript
// src/services/authService.js
import api from '../config/api';

export const login = async (email, password) => {
  try {
    console.log('🔐 Intentando login:', {
      email,
      apiUrl: api.defaults.baseURL
    });
    
    const response = await api.post('/auth/login/', {
      email,
      password
    });
    
    console.log('✅ Login exitoso:', response.data);
    return response.data;
    
  } catch (error) {
    console.error('❌ Error en login:', error.response?.data || error.message);
    throw error;
  }
};
```

---

## 🧪 Prueba de Concepto

Abre la consola del navegador en `https://bienestar.psicoadmin.xyz` y ejecuta:

```javascript
// Prueba manual con fetch
fetch('https://api.psicoadmin.xyz/api/auth/login/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Tenant-Schema': 'bienestar'
  },
  body: JSON.stringify({
    email: 'admin@bienestar.com',
    password: 'admin123'
  })
})
.then(res => res.json())
.then(data => console.log('✅ Respuesta:', data))
.catch(err => console.error('❌ Error:', err));
```

**Resultado esperado:**
```json
{
  "message": "Sesión iniciada exitosamente",
  "user": {
    "id": 49,
    "email": "admin@bienestar.com",
    "first_name": "Admin",
    "last_name": "Bienestar",
    "user_type": "admin"
  }
}
```

---

## 📋 Credenciales de Prueba

### BIENESTAR

| Tipo | Email | Password |
|------|-------|----------|
| Admin | `admin@bienestar.com` | `admin123` |
| Profesional | `dra.martinez@bienestar.com` | `demo123` |
| Paciente | `juan.perez@example.com` | `demo123` |

### MINDCARE

| Tipo | Email | Password |
|------|-------|----------|
| Admin | `admin@mindcare.com` | `admin123` |
| Profesional | `dr.garcia@mindcare.com` | `demo123` |
| Paciente | `maria.lopez@example.com` | `demo123` |

---

## 🔍 Verificación de Logs

Los logs del backend mostrarán:

```
INFO 🔍 [CustomTenantMiddleware] Hostname: api.psicoadmin.xyz
INFO 🎯 Header X-Tenant-Schema detectado: bienestar
INFO ✅ Tenant desde header: bienestar (ID: 2)
INFO 🗄️ PostgreSQL schema activado: bienestar
INFO 🔐 [Login] Intento de login - Email: admin@bienestar.com
INFO ✅ [Login] Validación exitosa
```

---

## 🚨 Errores Comunes

### Error 404: "Not Found"
```javascript
// ❌ MAL
const url = 'https://bienestar.psicoadmin.xyz/api/auth/login/';

// ✅ BIEN
const url = 'https://api.psicoadmin.xyz/api/auth/login/';
```

### Error 400: "Credenciales inválidas"
- **Causa**: No se está enviando el header `X-Tenant-Schema`
- **Solución**: El backend busca en el schema `public` donde no existe el usuario
- **Fix**: Agregar el header en cada petición

### CORS Error
- **Causa**: El backend solo permite CORS desde subdominios `*.psicoadmin.xyz`
- **Solución**: Ya está configurado correctamente en el backend

---

## 📞 Soporte

Si tienes dudas o errores:
1. Abre la consola del navegador (F12)
2. Ve a la pestaña "Network"
3. Busca la petición a `/api/auth/login/`
4. Verifica:
   - ✅ URL: debe ser `https://api.psicoadmin.xyz/api/auth/login/`
   - ✅ Headers: debe incluir `X-Tenant-Schema: bienestar`
   - ✅ Method: debe ser `POST`

---

## 📊 Arquitectura

```
┌─────────────────────────────────────────────────────────────┐
│                      ARQUITECTURA                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Frontend en Vercel (React):                                │
│  ┌───────────────────────────────────────────────┐         │
│  │  https://bienestar.psicoadmin.xyz             │         │
│  │  https://mindcare.psicoadmin.xyz              │         │
│  └─────────────────┬─────────────────────────────┘         │
│                    │                                         │
│                    │ POST /api/auth/login/                  │
│                    │ Headers:                               │
│                    │   X-Tenant-Schema: bienestar           │
│                    ↓                                         │
│  Backend en Render (Django):                                │
│  ┌───────────────────────────────────────────────┐         │
│  │  https://api.psicoadmin.xyz/api               │         │
│  │                                                │         │
│  │  Middleware detecta:                           │         │
│  │  1. Lee header X-Tenant-Schema                 │         │
│  │  2. Activa schema PostgreSQL correcto         │         │
│  │  3. Busca usuario en tabla del tenant         │         │
│  └───────────────────────────────────────────────┘         │
│                    │                                         │
│                    ↓                                         │
│  Base de Datos (Neon PostgreSQL):                          │
│  ┌───────────────────────────────────────────────┐         │
│  │  Schema: bienestar                             │         │
│  │    - users_customuser                         │         │
│  │    - appointments                             │         │
│  │    - ...                                      │         │
│  │                                                │         │
│  │  Schema: mindcare                             │         │
│  │    - users_customuser                         │         │
│  │    - appointments                             │         │
│  │    - ...                                      │         │
│  └───────────────────────────────────────────────┘         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## ✅ Checklist de Implementación

- [ ] Cambiar `API_BASE_URL` a `https://api.psicoadmin.xyz/api`
- [ ] Crear función `getTenantFromDomain()`
- [ ] Agregar interceptor de axios con header `X-Tenant-Schema`
- [ ] Probar login en consola del navegador
- [ ] Verificar que todas las rutas usen la instancia de axios configurada
- [ ] Eliminar cualquier referencia a `bienestar.psicoadmin.xyz/api`
- [ ] Testear en ambos subdominios (bienestar y mindcare)

---

**Última actualización:** 2025-11-06
**Versión del backend:** v2 - Con usuarios demo
**Estado:** ✅ Backend funcionando correctamente
