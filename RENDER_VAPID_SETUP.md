# 🔧 Configurar Variables VAPID en Render

## ❌ Error Actual
```
AttributeError: 'Settings' object has no attribute 'VAPID_PUBLIC_KEY'
```

Esto significa que las variables de entorno **NO están configuradas en Render**.

---

## ✅ Solución: Añadir Variables en Render Dashboard

### 📋 Paso 1: Acceder al Dashboard de Render

1. Ve a: https://dashboard.render.com/
2. Selecciona tu servicio: **backend_sp3** (o como se llame tu servicio Django)
3. En el menú lateral, haz clic en **"Environment"**

---

### 📋 Paso 2: Añadir las 3 Variables VAPID

Haz clic en **"Add Environment Variable"** para cada una de estas:

#### Variable 1: VAPID_PUBLIC_KEY
```
Key: VAPID_PUBLIC_KEY
Value: BNVdhBTDqH9WQRtYuLqy1VjA7QSEZPwlM0vgxmVn4K3a6to8unUoie_ZaqA8TzXAg49ExZ8PXqccm63T0tmq_j0
```

#### Variable 2: VAPID_PRIVATE_KEY
```
Key: VAPID_PRIVATE_KEY
Value: -----BEGIN PRIVATE KEY-----
MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEHBG0wawIBAQQgJ9ZKB26RDV217Xip
UofytQs9hzxHJHbUDEoPafphZz6hRANCAATVXYQUw6h/VkEbWLi6stVYwO0EhGT8
JTNL4MZlZ+Ct2uraPLp1KInv2WqgPE81wIOPRMWfD16nHJut09LZqv49
-----END PRIVATE KEY-----
```

⚠️ **IMPORTANTE para VAPID_PRIVATE_KEY:**
- Copia **TODO** el bloque, incluyendo las líneas `-----BEGIN PRIVATE KEY-----` y `-----END PRIVATE KEY-----`
- Render soporta valores multi-línea
- **NO** añadas comillas adicionales
- **NO** escapes los saltos de línea

#### Variable 3: VAPID_CLAIM_EMAIL
```
Key: VAPID_CLAIM_EMAIL
Value: admin@psicoadmin.xyz
```

---

### 📋 Paso 3: Guardar y Redesplegar

1. Haz clic en **"Save Changes"** al final de la página
2. Render automáticamente redesplegará tu servicio
3. Espera a que el despliegue termine (verás "Live" en verde)

---

### 📋 Paso 4: Verificar la Configuración

1. Abre el **Shell** de Render:
   - En tu servicio, ve a la pestaña **"Shell"**
   - O accede vía SSH

2. Ejecuta estos comandos:
   ```bash
   python manage.py shell
   ```

3. Dentro del shell de Django:
   ```python
   from django.conf import settings
   
   # Verificar clave pública
   print("PUBLIC KEY:", settings.VAPID_PUBLIC_KEY)
   
   # Verificar clave privada (primeras líneas)
   print("PRIVATE KEY:", settings.VAPID_PRIVATE_KEY[:50])
   
   # Verificar email
   print("CLAIM EMAIL:", settings.VAPID_CLAIM_EMAIL)
   ```

4. **Resultado esperado:**
   ```
   PUBLIC KEY: BNVdhBTDqH9WQRtYuLqy1VjA7QSEZPwlM0vgxmVn4K3a6...
   PRIVATE KEY: -----BEGIN PRIVATE KEY-----
   MIGHAgEAMBMGByqGSM...
   CLAIM EMAIL: admin@psicoadmin.xyz
   ```

5. Si ves cadenas vacías `""`, verifica que guardaste las variables correctamente.

---

### 📋 Paso 5: Probar el Endpoint Público

Desde tu terminal local o navegador, prueba:

```bash
curl https://api.psicoadmin.xyz/api/notifications/vapid-public-key/ \
  -H "X-Tenant-Schema: bienestar"
```

**Resultado esperado:**
```json
{
  "public_key": "BNVdhBTDqH9WQRtYuLqy1VjA7QSEZPwlM0vgxmVn4K3a6to8unUoie_ZaqA8TzXAg49ExZ8PXqccm63T0tmq_j0"
}
```

---

## 🔍 Troubleshooting

### ❌ "Settings object has no attribute VAPID_PUBLIC_KEY"
- **Causa:** Las variables no están en Render
- **Solución:** Sigue los pasos 1-3 arriba

### ❌ Las variables aparecen vacías `""`
- **Causa:** No se guardaron correctamente
- **Solución:** Verifica que hiciste clic en "Save Changes"

### ❌ Error al enviar notificaciones
- **Causa:** Clave privada mal formateada
- **Solución:** Verifica que copiaste TODO el bloque multi-línea sin comillas adicionales

### ❌ El servicio no redespliega automáticamente
- **Causa:** Configuración de Render
- **Solución:** Ve a "Manual Deploy" → "Deploy latest commit"

---

## 📸 Captura de Pantalla de Referencia

Tus variables en Render deberían verse así:

```
Environment Variables
┌─────────────────────┬──────────────────────────────────────────┐
│ Key                 │ Value                                    │
├─────────────────────┼──────────────────────────────────────────┤
│ VAPID_PUBLIC_KEY    │ BNVdhBTDqH9WQRtYuLqy1VjA7QSEZPwlM0... │
├─────────────────────┼──────────────────────────────────────────┤
│ VAPID_PRIVATE_KEY   │ -----BEGIN PRIVATE KEY-----              │
│                     │ MIGHAgEAMBMGByqGSM49AgEGCCqGSM49AwEH... │
│                     │ -----END PRIVATE KEY-----                │
├─────────────────────┼──────────────────────────────────────────┤
│ VAPID_CLAIM_EMAIL   │ admin@psicoadmin.xyz                     │
└─────────────────────┴──────────────────────────────────────────┘
```

---

## ✅ Una vez configurado correctamente

Podrás:
- ✅ Obtener la clave pública desde el frontend
- ✅ Suscribir dispositivos a notificaciones push
- ✅ Enviar notificaciones desde el backend
- ✅ Ver historial de notificaciones

---

## 📚 Recursos Adicionales

- **Documentación completa:** `PUSH_NOTIFICATIONS_GUIDE.md`
- **Implementación backend:** `PUSH_NOTIFICATIONS_IMPLEMENTATION.md`
- **Template de variables:** `.env_notifications_template`
- **Script de prueba:** `test_push_notifications.ps1`
