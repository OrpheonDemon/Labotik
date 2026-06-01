# Reporte de Modificaciones Recientes en el Sistema - Labotik

Este documento detalla los cambios realizados en el proyecto para corregir problemas de infraestructura, resolver conflictos de importación y ajustar el flujo del portal de pacientes para centralizar los cobros en recepción. Tu compañero(a) de desarrollo debe leer este reporte para sincronizar su entorno local.

---

## 🛠️ Resumen de Modificaciones

### 1. Resolución del Conflicto de Importaciones en FastAPI
*   **Problema previo:** El backend fallaba al iniciar arrojando `ModuleNotFoundError: No module named 'app.utils.payment_qr'; 'app.utils' is not a package`. Esto ocurría porque existía el archivo `backend/app/utils.py` y la carpeta `backend/app/utils/` en el mismo nivel, bloqueando las importaciones de la subcarpeta.
*   **Solución aplicada:**
    *   Se creó [__init__.py](file:///d:/LBTk/Labotik-Rotherick/backend/app/utils/__init__.py) convirtiendo a `app.utils` en un paquete formal de Python.
    *   Se portaron a este archivo de inicialización todas las utilidades de hashing (contraseñas) y generación de tokens JWT.
    *   Se **eliminó** el archivo conflictivo `backend/app/utils.py`.
    *   **Adaptación:** Cualquier importación que antes apuntara a `app.utils` seguirá respondiendo de forma idéntica, pero resolviéndose ahora desde `app.utils.__init__`.

### 2. Centralización del Flujo de Pagos (Remoción de Pagos en Portal de Paciente)
*   **Cambio en Regla de Negocio:** Siguiendo las directrices del laboratorio, los **pacientes no realizan pagos directamente en su portal**, sino que las solicitudes quedan registradas como *pendientes de pago* y son confirmadas/efectuadas manualmente por los **recepcionistas** en su dashboard dedicado.
*   **Modificaciones en la plantilla de paciente ([paciente_dashboard.html](file:///d:/LBTk/Labotik-Rotherick/frontend/templates/dashboard/paciente_dashboard.html)):**
    *   **Menú Lateral:** Se eliminó por completo la opción "Mis Pagos" del listado de navegación del paciente.
    *   **Contenedor Visual:** Se removió la sección `<section id="pagos">` encargada de renderizar la pasarela de pagos.
    *   **Scripts JavaScript:** Se removieron las funciones de carga de facturas (`loadPagosSection()`), la generación del modal con código QR (`generateQR()`) y las condiciones de enrutamiento interno para mantener la plantilla ligera y libre de referencias huertas.

### 3. Sincronización de Contraseñas y Entornos de Prueba
*   **MySQL Local:** Se actualizaron los scripts `check_db.py` y `check_users.py` con la contraseña de MySQL `0000` (coincidiendo con tu base de datos y la configuración del `.env`).
*   **Variables de Entorno:** Se copió el archivo `.env` del backend a la raíz para asegurar que cualquier script ejecutado desde el directorio principal pueda resolver correctamente las variables de configuración sin crashear.

---

## 🚀 Guía de Adaptación para tu Compañero

Si eres el compañero de desarrollo y acabas de descargar esta rama (`Orpheus`), sigue estos pasos para sincronizar tu entorno local:

### Paso 1: Reconstrucción del Entorno Virtual (`venv`)
Dado que el entorno virtual contiene rutas absolutas de tu máquina local, no se debe subir a GitHub. Si experimentas fallas en el intérprete de Python, elimínalo y vuelve a crearlo:
```bash
# 1. Elimina la carpeta 'venv' si existe
# 2. Crea un nuevo entorno virtual local
python -m venv venv

# 3. Activa tu entorno virtual
# En Windows (CMD):
venv\Scripts\activate.bat
# En Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# 4. Instala todas las dependencias
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt
```

### Paso 2: Configuración de Base de Datos MySQL
1. Asegúrate de tener MySQL activo en el puerto `3306`.
2. Modifica la contraseña de conexión en tu archivo `backend/.env` (línea 1, `DATABASE_URL`) con tus credenciales de base de datos locales si difieren de `0000`.
3. Si cambiaste la contraseña en `.env`, asegúrate de actualizarla en las líneas de conexión de los scripts:
   - `check_db.py` (Línea 6, `password='tu_password'`)
   - `check_users.py` (Línea 12, `password='tu_password'`)

### Paso 3: Iniciar Servidores
Puedes levantar Ollama (IA), el backend de FastAPI y el frontend de Django usando los scripts automatizados provistos en la raíz:
*   **start_servers.pyw:** Inicia todos los servicios en segundo plano de manera transparente.
*   **run_servers.bat:** Inicia los servicios en ventanas de comandos individuales para monitorear los logs en tiempo real.
*   **stop_servers.py:** Detiene todos los procesos y libera los puertos de forma limpia.
