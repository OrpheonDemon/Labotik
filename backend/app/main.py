from fastapi import FastAPI
from app.database import engine, Base
from app.routers import (
    areas, pruebas, pacientes, medicos, laboratoristas,
    solicitudes, resultados, reportes, facturas, pagos, auth
)
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Laboratorio Clínico API", version="1.0")

# Configurar CORS (ajusta los dominios permitidos en producción)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # IMPORTANTE: En producción usar dominios específicos, ej: ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def init_db():
    async with engine.begin() as conn:
        # Crea las tablas si no existen (opcional, ya deberían existir por el SQL)
        await conn.run_sync(Base.metadata.create_all)

# Incluir routers
app.include_router(auth.router)
app.include_router(areas.router)
app.include_router(pruebas.router)
app.include_router(pacientes.router)
app.include_router(medicos.router)
app.include_router(laboratoristas.router)
app.include_router(solicitudes.router)
app.include_router(resultados.router)
app.include_router(reportes.router)
app.include_router(facturas.router)
app.include_router(pagos.router)

@app.get("/")
async def root():
    return {"message": "API Laboratorio Clínico funcionando correctamente"}