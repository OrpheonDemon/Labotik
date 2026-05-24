from datetime import datetime
import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app import schemas, crud
from app.database import get_db
from app.dependencies import require_medico, require_paciente, get_current_active_user
from app.models import DiagnosticoPredictivo, Solicitud, DetalleSolicitud, Resultado, Prueba
from app.services.ollama_service import OllamaService
from app.ai_engine import (
    OllamaClient,
    ClinicalInterpreter,
    AnomalyDetector,
    PriorityEngine,
    AuditService,
    EmbeddingsService,
    RAGEngine,
    ClinicalAssistant,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/diagnosticos", tags=["Asistente Clínico IA"])

# Instanciar servicios IA
ollama_service = OllamaService(model="medgemma", base_url="http://localhost:11434")
ollama_client = OllamaClient(model="medgemma", base_url="http://localhost:11434")
clinical_interpreter = ClinicalInterpreter(ollama_client)
anomaly_detector = AnomalyDetector()
priority_engine = PriorityEngine()
audit_service = AuditService()
embeddings_service = EmbeddingsService()
rag_engine = RAGEngine(embeddings_service, ollama_client)
clinical_assistant = ClinicalAssistant(rag_engine, ollama_client)


class AssistantQuery(BaseModel):
    question: str
    patient_context: Optional[str] = None


class ClinicalPayload(BaseModel):
    resultados: list[dict]
    patient_context: Optional[str] = None


class PriorityPayload(BaseModel):
    resultados: list[dict]
    paciente: Optional[dict] = None


class AnomalyPayload(BaseModel):
    resultados: list[dict]

@router.post("/{id_solicitud}/generar", response_model=schemas.DiagnosticoPreventivoOut)
async def generar_diagnostico_predictivo(
    id_solicitud: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_medico)
):
    """
    Genera un informe del Asistente Clínico IA con análisis asistido y recomendaciones preliminares.
    Solo médicos pueden generar estos informes.
    """
    # Obtener solicitud
    stmt = select(Solicitud).where(Solicitud.id_solicitud == id_solicitud)
    result = await db.execute(stmt)
    solicitud = result.scalar_one_or_none()
    
    if not solicitud:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    
    # Obtener todos los resultados de la solicitud
    stmt = select(DetalleSolicitud, Resultado, Prueba).join(
        Resultado, DetalleSolicitud.id_detalle == Resultado.id_detalle
    ).join(
        Prueba, DetalleSolicitud.id_prueba == Prueba.id_prueba
    ).where(
        DetalleSolicitud.id_solicitud == id_solicitud
    )
    result = await db.execute(stmt)
    detalles_con_resultados = result.all()
    
    if not detalles_con_resultados:
        raise HTTPException(status_code=400, detail="No hay resultados disponibles para este diagnóstico")
    
    # Compilar datos clínicos
    datos_clinicos = compilar_datos_clinicos(detalles_con_resultados)
    
    # Llamar a ollama con medgemma para análisis
    try:
        diagnostico_actual, confianza, predicciones, factores_riesgo, recomendaciones = await ollama_service.analizar_resultados(
            datos_clinicos=datos_clinicos,
            id_paciente=solicitud.id_paciente
        )
    except Exception as e:
        logger.error(f"Error al generar diagnóstico con ollama: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al generar diagnóstico: {str(e)}")
    
    # Verificar si ya existe diagnóstico para esta solicitud
    diagnostico_existente = await crud.diagnostico_crud.get_by_solicitud(db, id_solicitud)
    
    if diagnostico_existente:
        # Actualizar diagnóstico existente
        update_data = schemas.DiagnosticoPreventivoUpdate(
            diagnostico_actual=diagnostico_actual,
            confianza_actual=confianza,
            predicciones=predicciones,
            factores_riesgo=factores_riesgo,
            recomendaciones=recomendaciones
        )
        diagnostico = await crud.diagnostico_crud.update(db, diagnostico_existente.id_diagnostico, update_data)
    else:
        # Crear nuevo diagnóstico
        create_data = schemas.DiagnosticoPreventivoCreate(
            id_solicitud=id_solicitud,
            id_paciente=solicitud.id_paciente,
            id_medico=current_user["user"].id_medico,
            diagnostico_actual=diagnostico_actual,
            confianza_actual=confianza
        )
        diagnostico = await crud.diagnostico_crud.create(db, create_data)
        
        # Actualizar con predicciones, factores de riesgo y recomendaciones
        update_data = schemas.DiagnosticoPreventivoUpdate(
            predicciones=predicciones,
            factores_riesgo=factores_riesgo,
            recomendaciones=recomendaciones
        )
        diagnostico = await crud.diagnostico_crud.update(db, diagnostico.id_diagnostico, update_data)
    
    # Registrar creación/actualización y alimentar el motor RAG
    audit_service.record_event(
        'generar_diagnostico',
        current_user.get('user').id_medico if current_user and current_user.get('user') else None,
        {
            'id_solicitud': id_solicitud,
            'id_paciente': solicitud.id_paciente,
            'id_diagnostico': diagnostico.id_diagnostico,
            'confianza_actual': confianza,
        }
    )

    rag_engine.index_document(
        f"diagnostico_{diagnostico.id_diagnostico}",
        json.dumps({
            'diagnostico_actual': diagnostico_actual,
            'predicciones': predicciones,
            'factores_riesgo': factores_riesgo,
            'recomendaciones': recomendaciones,
        }, ensure_ascii=False),
        metadata={
            'id_paciente': solicitud.id_paciente,
            'id_solicitud': id_solicitud,
            'id_diagnostico': diagnostico.id_diagnostico,
        }
    )

    return diagnostico

@router.post("/interpretar")
async def interpretar_resultados(payload: ClinicalPayload):
    """Genera una interpretación clínica asistida usando el motor IA."""
    interpretation = await clinical_interpreter.interpret(payload.resultados, payload.patient_context)
    audit_service.record_event("interpretar_resultados", None, {
        "resultados_count": len(payload.resultados),
        "patient_context": bool(payload.patient_context)
    })
    return {
        "tipo": "interpretacion_clinica",
        "resultados": interpretation
    }

@router.post("/anomalias")
async def detectar_anomalias(payload: AnomalyPayload):
    """Detecta anomalías, errores y alertas en los resultados clínicos."""
    findings = anomaly_detector.detect(payload.resultados)
    audit_service.record_event("detectar_anomalias", None, {
        "resultados_count": len(payload.resultados),
        "findings_count": len(findings)
    })
    return {
        "tipo": "anomalias_y_errores",
        "count": len(findings),
        "findings": findings
    }

@router.post("/prioridad")
async def calcular_prioridad(payload: PriorityPayload):
    """Calcula el puntaje de prioridad clínica para los resultados."""
    score = priority_engine.score(payload.resultados, payload.paciente)
    audit_service.record_event("calcular_prioridad", None, {
        "resultados_count": len(payload.resultados),
        "paciente_incluido": payload.paciente is not None
    })
    return {
        "tipo": "prioridad_clinica",
        "score": score
    }

@router.post("/chat")
async def asistente_clinico_chat(query: AssistantQuery):
    """Consulta al copiloto clínico IA con contexto médico y RAG local."""
    response = await clinical_assistant.ask(query.question, query.patient_context)
    audit_service.record_event("chat_query", None, {"question": query.question})
    return response

@router.post("/indexar")
async def indexar_diagnosticos(db: AsyncSession = Depends(get_db)):
    """Indexa los diagnósticos existentes en el motor RAG para mejorar respuestas clínicas."""
    diagnosticos = await crud.diagnostico_crud.get_multi(db, skip=0, limit=1000)
    for diagnostico in diagnosticos:
        document_text = json.dumps({
            'diagnostico_actual': diagnostico.diagnostico_actual,
            'predicciones': diagnostico.predicciones,
            'factores_riesgo': diagnostico.factores_riesgo,
            'recomendaciones': diagnostico.recomendaciones,
        }, ensure_ascii=False)
        rag_engine.index_document(
            f"diagnostico_{diagnostico.id_diagnostico}",
            document_text,
            metadata={
                'id_paciente': diagnostico.id_paciente,
                'id_solicitud': diagnostico.id_solicitud,
                'id_diagnostico': diagnostico.id_diagnostico,
            }
        )
    audit_service.record_event("indexar_diagnosticos", None, {"indexed_count": len(diagnosticos)})
    return {"indexed_count": len(diagnosticos)}

@router.get("/auditoria")
async def ver_auditoria():
    """Recupera el registro de auditoría del asistente clínico."""
    return audit_service.get_audit_log()

@router.get("/{id_diagnostico}", response_model=schemas.DiagnosticoPreventivoOut)
async def get_diagnostico(
    id_diagnostico: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Obtener un informe generado por el Asistente Clínico IA específico."""
    diagnostico = await crud.diagnostico_crud.get(db, id_diagnostico)
    
    if not diagnostico:
        raise HTTPException(status_code=404, detail="Diagnóstico no encontrado")
    
    # Validar acceso: paciente solo ve sus propios diagnósticos, médico ve todos
    if current_user["rol"] == "paciente":
        if diagnostico.id_paciente != current_user["user"].id_paciente:
            raise HTTPException(status_code=403, detail="No tienes acceso a este diagnóstico")
    
    return diagnostico

@router.get("/paciente/{id_paciente}", response_model=list[schemas.DiagnosticoPreventivoOut])
async def get_diagnosticos_paciente(
    id_paciente: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(get_current_active_user)
):
    """Obtener todos los informes del Asistente Clínico IA de un paciente."""
    # Validar acceso
    if current_user["rol"] == "paciente":
        if id_paciente != current_user["user"].id_paciente:
            raise HTTPException(status_code=403, detail="No tienes acceso a esos diagnósticos")
    elif current_user["rol"] not in ["medico", "administrador", "laboratorista"]:
        raise HTTPException(status_code=403, detail="No tienes permisos para ver diagnósticos")
    
    diagnosticos = await crud.diagnostico_crud.get_by_paciente(db, id_paciente)
    return diagnosticos

@router.delete("/{id_diagnostico}")
async def delete_diagnostico(
    id_diagnostico: int,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_medico)
):
    """Eliminar (borrado lógico) un informe generado por el Asistente Clínico IA."""
    diagnostico = await crud.diagnostico_crud.get(db, id_diagnostico)
    
    if not diagnostico:
        raise HTTPException(status_code=404, detail="Diagnóstico no encontrado")
    
    # Solo el médico que lo creó o un administrador pueden borrarlo
    if current_user["rol"] == "medico" and diagnostico.id_medico != current_user["user"].id_medico:
        raise HTTPException(status_code=403, detail="No puedes eliminar diagnósticos de otros médicos")
    
    deleted = await crud.diagnostico_crud.soft_delete(db, id_diagnostico)
    
    if not deleted:
        raise HTTPException(status_code=400, detail="No se pudo eliminar el diagnóstico")
    
    return {"message": "Diagnóstico eliminado correctamente"}


def compilar_datos_clinicos(detalles_con_resultados: list) -> dict:
    """Compila los datos clínicos de los resultados para enviar a ollama."""
    datos = {
        "pruebas": [],
        "timestamp": datetime.now().isoformat()
    }
    
    for detalle, resultado, prueba in detalles_con_resultados:
        if resultado:
            prueba_data = {
                "nombre": prueba.nombre,
                "resultado": resultado.resultado,
                "valor_referencia": prueba.valor_referencia,
                "unidad": prueba.unidad,
                "es_anormal": bool(resultado.es_anormal),
                "observacion": resultado.observacion or ""
            }
            datos["pruebas"].append(prueba_data)
    
    return datos
