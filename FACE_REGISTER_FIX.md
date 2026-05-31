# Correcciones al Sistema de Registro Facial (Face Register)

## Problemas Identificados y Corregidos

### 1. **Error en el mapeo de `tabla_usuario` en `dependencies.py`**

**Problema:**
El código original en `dependencies.py` línea 32 tenía un mapeo incorrecto:
```python
# Código anterior (incorrecto)
"tabla_usuario": rol + "s" if rol != "recepcionista" else "administradores"
```

Esto causaba que:
- `administrador` → `administradors` (incorrecto, debería ser `administradores`)
- `recepcionista` → `administradores` (mapeo arbitrario sin relación con la tabla real)

**Solución:**
Se implementó un mapeo explícrito y correcto:
```python
rol_to_table = {
    "paciente": "pacientes",
    "medico": "medicos",
    "laboratorista": "laboratoristas",
    "administrador": "administradores",
    "recepcionista": "administradores"
}
tabla_usuario = rol_to_table.get(rol, ...)
```

**Archivos modificados:** `backend/app/dependencies.py`

---

### 2. **Mejora en la validación de `id_usuario` en `face_auth.py`**

**Problema:**
El endpoint `/auth/face/register` no validaba correctamente si `id_usuario` estaba presente en el token JWT, lo que causaba errores silenciosos.

**Solución:**
Se agregó logging detallado y un mensaje de error más claro cuando el token no contiene la información necesaria:
```python
if not user_id or not user_table:
    logger.error(f"Error: user_id={user_id}, user_table={user_table}, current_user={current_user}")
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="No se pudo identificar al usuario. El token no contiene la información necesaria."
    )
```

**Archivos modificados:** `backend/app/routers/face_auth.py`

---

### 3. **Mejora en el cálculo de calidad de imagen en `face_service.py`**

**Problema:**
La calidad de la imagen se calculaba solo basada en el tamaño del rostro detectado (`face_size / 5000`), lo cual no era un buen indicador de calidad real.

**Solución:**
Se implementó un algoritmo de calidad más sofisticado que considera:
- **Tamaño del rostro** (40%): `face_size / 10000`
- **Proporción en la imagen** (30%): Idealmente 10-30% del área total
- **Posición centrada** (30%): Distancia del centro del rostro al centro de la imagen

```python
size_quality = min(1.0, face_size / 10000)
ratio_quality = min(1.0, max(0.0, (face_ratio - 0.05) / 0.15))
position_quality = max(0.0, 1.0 - (center_dist / max_dist))
quality = (size_quality * 0.4 + ratio_quality * 0.3 + position_quality * 0.3)
```

**Archivos modificados:** `backend/app/services/face_service.py`

---

### 4. **Mejora en los mensajes de error en `face_service.py`**

**Problema:**
Los mensajes de error no eran lo suficientemente descriptivos para ayudar al usuario a entender qué salió mal.

**Solución:**
Se mejoraron los mensajes de error:
- "No se detectó ningún rostro..." → "... Asegúrese de que haya suficiente iluminación y que el rostro sea visible."
- "Servicio no disponible" → "... Instale deepface y opencv-python."
- Se agregó traceback en el logging para debugging

**Archivos modificados:** `backend/app/services/face_service.py`

---

### 5. **Mejora en el frontend para manejo de errores de cámara**

**Problema:**
El frontend no manejaba adecuadamente los diferentes tipos de errores de cámara.

**Solución:**
Se agregó manejo específico para cada tipo de error:
```javascript
if (error.name === 'NotAllowedError') {
    errorMsg = 'Permiso de cámara denegado. Por favor, permita el acceso en su navegador.';
} else if (error.name === 'NotFoundError') {
    errorMsg = 'No se encontró ninguna cámara. Por favor, conecte una cámara.';
} else if (error.name === 'NotReadableError') {
    errorMsg = 'La cámara está siendo usada por otra aplicación.';
}
```

También se mejoró la obtención del token para soportar tanto `sessionStorage` como cookies.

**Archivos modificados:** `frontend/authentication/templates/face_register.html`

---

## Archivos Modificados

1. `backend/app/dependencies.py` - Corrección de mapeo de tabla_usuario
2. `backend/app/routers/face_auth.py` - Mejora en validación y logging
3. `backend/app/services/face_service.py` - Mejora en cálculo de calidad y mensajes de error
4. `frontend/authentication/templates/face_register.html` - Mejora en manejo de errores de cámara

## Archivos Nuevos

1. `backend/check_face_registration.py` - Script de verificación del sistema

## Cómo Verificar que el Sistema Funciona

### 1. Ejecutar el script de verificación:
```bash
cd backend
python check_face_registration.py
```

Este script verifica:
- ✓ Dependencias instaladas (deepface, opencv-python, numpy, sqlalchemy)
- ✓ Servicio facial disponible
- ✓ Base de datos y tablas existentes
- ✓ Clasificador de caras de OpenCV

### 2. Verificar que el backend está corriendo:
```bash
cd backend
python run_server.py
```

### 3. Verificar que el frontend está corriendo:
```bash
cd frontend
python manage.py runserver
```

### 4. Probar el flujo completo:
1. Iniciar sesión con credenciales tradicionales
2. Navegar a `/face-register/`
3. Permitir acceso a la cámara
4. Capturar 3 imágenes desde diferentes ángulos
5. Verificar que el registro sea exitoso

## Requisitos del Sistema

### Dependencias de Python:
```bash
pip install deepface opencv-python numpy sqlalchemy aiomysql pymysql
```

### Requisitos del Navegador:
- Permiso de cámara habilitado
- HTTPS o localhost (los navegadores requieren contexto seguro para acceso a cámara)

## Posibles Problemas y Soluciones

### Error: "Servicio de reconocimiento facial no disponible"
**Causa:** Falta instalar deepface o opencv-python
**Solución:** `pip install deepface opencv-python`

### Error: "No se detectó ningún rostro en la imagen"
**Causas posibles:**
- Iluminación insuficiente
- Rostro muy pequeño en la imagen
- Rostro en ángulo extremo
- Cámara muy lejos
**Solución:** Mejorar iluminación, acercar el rostro, mirar directamente a la cámara

### Error: "No se pudo identificar al usuario"
**Causa:** El token JWT no contiene `id_usuario`
**Solución:** Asegurarse de haber iniciado sesión correctamente antes de acceder al registro facial

### Error: "Permiso de cámara denegado"
**Causa:** El navegador bloqueó el acceso a la cámara
**Solución:** Permitir acceso a la cámara en la configuración del navegador

## Notas Importantes

1. **Primera ejecución:** La primera vez que se usa DeepFace, descarga automáticamente los modelos (puede tardar varios minutos).

2. **Rendimiento:** El reconocimiento facial puede ser lento en la primera ejecución debido a la carga de modelos.

3. **Seguridad:** Los embeddings faciales se almacenan de forma segura en la base de datos y no se puede revertir a la imagen original.

4. **Límites:** Cada usuario puede registrar hasta 3 rostros diferentes para mejorar la precisión del reconocimiento.