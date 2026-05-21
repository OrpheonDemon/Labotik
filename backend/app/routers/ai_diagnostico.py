from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional

from app.database import get_db
from app.models import Solicitud, DetalleSolicitud, Prueba, Resultado, Paciente

router = APIRouter(
    prefix="/ai",
    tags=["Inteligencia Artificial"]
)

@router.post("/diagnostico/{id_solicitud}")
async def generar_diagnostico(
    id_solicitud: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Simula la llamada a un modelo de IA (ej. Gemini) para generar un diagnóstico
    preventivo basado en los resultados de laboratorio.
    """
    # Obtener la solicitud
    stmt = select(Solicitud).where(Solicitud.id_solicitud == id_solicitud)
    result = await db.execute(stmt)
    solicitud = result.scalar_one_or_none()
    
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
        
    if solicitud.estado != 'completado':
        raise HTTPException(status_code=400, detail="Los resultados aún no están listos para ser analizados")

    # Obtener el paciente
    stmt = select(Paciente).where(Paciente.id_paciente == solicitud.id_paciente)
    result = await db.execute(stmt)
    paciente = result.scalar_one_or_none()

    # Recopilar resultados
    # Por simplicidad, simularemos la respuesta de la IA.
    # En producción aquí se integraría google-generativeai con un prompt detallado.
    
    prompt_usado = f"Analiza los resultados del paciente {paciente.nombre} (Edad: {paciente.fecha_nacimiento}) para la solicitud {id_solicitud}."
    
    respuesta_simulada = {
        "resumen": "El paciente presenta indicadores generales estables, aunque se observa una leve elevación en marcadores inflamatorios.",
        "posibles_riesgos": [
            "Proceso inflamatorio o infeccioso agudo (basado en PCR elevada).",
            "Riesgo cardiovascular moderado si los niveles de estrés no se controlan."
        ],
        "recomendaciones_preventivas": [
            "Aumentar ingesta de líquidos.",
            "Realizar perfil lipídico de control en 3 meses.",
            "Agendar evaluación clínica general."
        ],
        "nota_legal": "Este es un diagnóstico preventivo generado por IA asistencial. No reemplaza el criterio del profesional de salud."
    }

    return respuesta_simulada
