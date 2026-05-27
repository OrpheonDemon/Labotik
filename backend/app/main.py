from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.database import engine, Base
from app.routers import (
    areas, pruebas, pacientes, medicos, laboratoristas, administradores,
    solicitudes, resultados, reportes, facturas, pagos, auth, ai
)
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
import logging

logger = logging.getLogger(__name__)

app = FastAPI(title="Laboratorio Clínico API", version="1.0")

# Configurar CORS (ajusta los dominios permitidos en producción)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost",
        "http://127.0.0.1",
    ],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:[0-9]{1,5})?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
    max_age=3600,
)


@app.on_event("startup")
async def init_db():
    async with engine.begin() as conn:
        # Crea las tablas si no existen (opcional, ya deberían existir por el SQL)
        await conn.run_sync(Base.metadata.create_all)

        # Asegurar que la tabla `resultados` existe con la estructura esperada.
        # Usamos CREATE TABLE IF NOT EXISTS para no romper esquemas existentes.
        try:
            await conn.execute(text(
                """
                CREATE TABLE IF NOT EXISTS resultados (
                    id_resultado INT PRIMARY KEY,
                    id_detalle INT NOT NULL,
                    resultado VARCHAR(100) NOT NULL,
                    observacion TEXT,
                    estado ENUM('pendiente','registrado','reportado') NOT NULL DEFAULT 'pendiente',
                    validado_por VARCHAR(20),
                    fecha_validacion DATETIME,
                    es_anormal INT DEFAULT 0,
                    activo INT DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB;
                """
            ))
            logger.info("Tabla 'resultados' asegurada en la base de datos.")
        except Exception:
            logger.exception("No se pudo crear/verificar la tabla 'resultados'.")

# Incluir routers
app.include_router(auth.router)
app.include_router(areas.router)
app.include_router(pruebas.router)
app.include_router(pacientes.router)
app.include_router(medicos.router)
app.include_router(laboratoristas.router)
app.include_router(administradores.router)
app.include_router(solicitudes.router)
app.include_router(resultados.router)
app.include_router(reportes.router)
app.include_router(facturas.router)
app.include_router(pagos.router)
app.include_router(ai.router)

@app.get("/")
async def root():
    return {"message": "API Laboratorio Clínico funcionando correctamente"}


@app.get('/health')
async def health():
    # Simple health check endpoint — intenta un SELECT 1
    from sqlalchemy import text
    try:
        async with engine.connect() as conn:
            await conn.execute(text('SELECT 1'))
        return {"status": "ok", "database": "connected"}
    except Exception as e:
        logger.exception('Health check DB failed')
        return {"status": "error", "database": "disconnected", "detail": str(e)}


@app.get('/test')
async def test():
    return {"message": "Test endpoint working", "cors": "enabled"}


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception during request: %s", exc)
    origin = request.headers.get("origin")
    headers = {}
    if origin:
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"
    status_code = getattr(exc, "status_code", 500)
    detail = getattr(exc, "detail", "Error interno del servidor")
    return JSONResponse(status_code=status_code, content={"detail": detail}, headers=headers)