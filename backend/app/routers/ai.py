from typing import Any, Optional

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from app.ai_engine import (
    OllamaClient,
    ClinicalInterpreter,
    AnomalyDetector,
    PriorityEngine,
    AuditService,
    EmbeddingsService,
    RAGEngine,
    ClinicalAssistant,
    PatientAnalyzer,
    ResultAnalyzer,
)
from app.dependencies import get_db
from app.crud import (
    paciente_crud,
    resultado_crud,
    detalle_solicitud_crud,
    prueba_crud,
    solicitud_crud,
)

router = APIRouter(prefix="/ai", tags=["Asistente Clínico IA"])

# Inicializar clientes y analizadores
ollama_client = OllamaClient(model="medgemma", base_url="http://localhost:11434")
clinical_interpreter = ClinicalInterpreter(ollama_client)
anomaly_detector = AnomalyDetector()
priority_engine = PriorityEngine()
audit_service = AuditService()
embeddings_service = EmbeddingsService()
rag_engine = RAGEngine(embeddings_service, ollama_client)
clinical_assistant = ClinicalAssistant(rag_engine, ollama_client)
patient_analyzer = PatientAnalyzer(ollama_client)
result_analyzer = ResultAnalyzer(ollama_client)


class ResultPayload(BaseModel):
    resultados: list[dict[str, Any]]
    patient_context: Optional[str] = None


class PriorityPayload(BaseModel):
    resultados: list[dict[str, Any]]
    paciente: Optional[dict[str, Any]] = None


class ChatPayload(BaseModel):
    question: str
    patient_context: Optional[str] = None


class PatientAnalysisPayload(BaseModel):
    patient_id: str
    include_history: bool = True


class ResultAnalysisPayload(BaseModel):
    patient_id: str
    result_id: int
    include_related: bool = True



@router.post("/analyze")
async def ai_analyze(payload: ResultPayload):
    interpretation = await clinical_interpreter.interpret(payload.resultados, payload.patient_context)
    priority = priority_engine.score(payload.resultados, None)
    anomalies = anomaly_detector.detect(payload.resultados)

    audit_service.record_event("ai_analyze", None, {
        "resultados_count": len(payload.resultados),
        "priority": priority.get("priority"),
        "anomaly_count": len(anomalies),
    })

    return {
        "hallazgos_relevantes": interpretation.get("observaciones", []),
        "interpretacion_clinica": interpretation.get("diagnostico_sugestivo", ""),
        "alertas_criticas": priority.get("alerts", []),
        "anomalias_detectadas": [
            f"{item.get('tipo')}: {item.get('mensaje')}" for item in anomalies
        ],
        "prioridad": priority.get("priority", "normal"),
        "recomendaciones": [interpretation.get("recomendaciones")] if interpretation.get("recomendaciones") else [],
        "requiere_revision_humana": True,
    }


@router.post("/interpret")
async def ai_interpret(payload: ResultPayload):
    interpretation = await clinical_interpreter.interpret(payload.resultados, payload.patient_context)
    audit_service.record_event("ai_interpret", None, {
        "resultados_count": len(payload.resultados),
    })
    return {
        "tipo": "interpretacion_clinica",
        "interpretacion": interpretation,
    }


@router.post("/prioritize")
async def ai_prioritize(payload: PriorityPayload):
    score = priority_engine.score(payload.resultados, payload.paciente)
    audit_service.record_event("ai_prioritize", None, {
        "resultados_count": len(payload.resultados),
        "patient_info_present": payload.paciente is not None,
    })
    return {
        "tipo": "prioridad_clinica",
        "prioridad": score.get("priority"),
        "score": score.get("score"),
        "alertas": score.get("alerts", []),
    }


@router.post("/chat")
async def ai_chat(payload: ChatPayload):
    response = await clinical_assistant.ask(payload.question, payload.patient_context)
    audit_service.record_event("ai_chat", None, {
        "question": payload.question,
    })
    return response


@router.get("/history")
async def ai_history(limit: int = Query(50, ge=1, le=200)):
    history = audit_service.get_audit_log(limit)
    return {
        "tipo": "historial_ia",
        "evento_count": len(history),
        "historial": history,
    }


@router.post("/patient-analysis")
async def analyze_patient_integral(
    payload: PatientAnalysisPayload,
    db: AsyncSession = Depends(get_db)
):
    """
    Análisis clínico integral de un paciente.
    Incluye análisis del perfil general y correlaciones.
    """
    try:
        # Obtener datos del paciente
        patient = await paciente_crud.get(db, payload.patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Paciente no encontrado")

        # Convertir a diccionario
        patient_dict = {
            "id_paciente": patient.id_paciente,
            "nombre": patient.nombre,
            "apellido_paterno": patient.apellido_paterno,
            "apellido_materno": patient.apellido_materno or "",
            "fecha_nacimiento": patient.fecha_nacimiento,
            "genero": patient.genero,
            "tipo_sangre": patient.tipo_sangre,
            "alergias": patient.alergias,
        }

        # Obtener historiales si se solicita
        medical_history = None
        recent_results = None

        if payload.include_history:
            # Obtener solicitudes del paciente
            from sqlalchemy import select
            solicitudes_stmt = select(solicitud_crud.model).where(
                solicitud_crud.model.id_paciente == payload.patient_id,
                solicitud_crud.model.activo == 1,
                solicitud_crud.model.estado == "completado"
            )
            solicitudes_result = await db.execute(solicitudes_stmt)
            solicitudes = solicitudes_result.scalars().all()

            if solicitudes:
                medical_history = []
                recent_results = []

                for solicitud in solicitudes[-5:]:  # Últimas 5 solicitudes
                    # Obtener detalles y resultados
                    detalles_stmt = select(detalle_solicitud_crud.model).where(
                        detalle_solicitud_crud.model.id_solicitud == solicitud.id_solicitud
                    )
                    detalles_result = await db.execute(detalles_stmt)
                    detalles = detalles_result.scalars().all()

                    for detalle in detalles:
                        # Obtener resultados
                        resultados_stmt = select(resultado_crud.model).where(
                            resultado_crud.model.id_detalle == detalle.id_detalle
                        )
                        resultados_result = await db.execute(resultados_stmt)
                        resultados = resultados_result.scalars().all()

                        # Obtener datos de prueba
                        prueba = await prueba_crud.get(db, detalle.id_prueba)

                        for resultado in resultados:
                            recent_results.append({
                                "nombre_prueba": prueba.nombre if prueba else "Desconocida",
                                "valor": resultado.resultado,
                                "unidad": prueba.unidad if prueba else "",
                                "rango_referencia": prueba.valor_referencia if prueba else "N/A",
                                "estado": "anormal" if resultado.es_anormal else "normal",
                                "fecha": resultado.created_at.isoformat() if resultado.created_at else "",
                            })

                    medical_history.append({
                        "fecha": solicitud.fecha_solicitud.isoformat() if solicitud.fecha_solicitud else "",
                        "hallazgos": "Solicitud completada",
                        "prioridad": solicitud.prioridad,
                    })

        # Realizar análisis
        analysis_result = await patient_analyzer.analyze_patient(
            patient_dict,
            medical_history,
            recent_results,
        )

        # Registrar evento
        audit_service.record_event("patient_analysis", payload.patient_id, {
            "patient_name": patient_dict.get("nombre"),
            "include_history": payload.include_history,
        })

        return analysis_result

    except HTTPException:
        raise
    except Exception as exc:
        audit_service.record_event("patient_analysis_error", payload.patient_id, {
            "error": str(exc)
        })
        raise HTTPException(status_code=500, detail=f"Error en análisis: {str(exc)}")


@router.post("/result-analysis")
async def analyze_result_specific(
    payload: ResultAnalysisPayload,
    db: AsyncSession = Depends(get_db)
):
    """
    Análisis clínico específico de un resultado.
    Proporciona interpretación detallada del resultado individual.
    """
    try:
        # Obtener datos del paciente
        patient = await paciente_crud.get(db, payload.patient_id)
        if not patient:
            raise HTTPException(status_code=404, detail="Paciente no encontrado")

        # Obtener resultado
        resultado = await resultado_crud.get(db, payload.result_id)
        if not resultado:
            raise HTTPException(status_code=404, detail="Resultado no encontrado")

        # Obtener detalle de solicitud
        detalle = await detalle_solicitud_crud.get(db, resultado.id_detalle)
        if not detalle:
            raise HTTPException(status_code=404, detail="Detalle de solicitud no encontrado")

        # Obtener prueba
        prueba = await prueba_crud.get(db, detalle.id_prueba)
        if not prueba:
            raise HTTPException(status_code=404, detail="Prueba no encontrada")

        # Construir diccionarios
        patient_dict = {
            "id_paciente": patient.id_paciente,
            "nombre": patient.nombre,
            "apellido_paterno": patient.apellido_paterno,
            "fecha_nacimiento": patient.fecha_nacimiento,
            "genero": patient.genero,
        }

        result_dict = {
            "id_resultado": resultado.id_resultado,
            "nombre_prueba": prueba.nombre,
            "valor": float(resultado.resultado) if resultado.resultado else 0,
            "unidad": prueba.unidad or "",
            "rango_min": 0,
            "rango_max": 100,
            "rango_referencia": prueba.valor_referencia or "N/A",
            "contexto_clinico": resultado.observacion or "No especificado",
        }

        # Parsear rango de referencia si es posible
        if prueba.valor_referencia:
            try:
                import re
                parts = re.findall(r'[\d.]+', str(prueba.valor_referencia))
                if len(parts) >= 2:
                    result_dict["rango_min"] = float(parts[0])
                    result_dict["rango_max"] = float(parts[1])
            except Exception:
                pass

        # Obtener biomarcadores relacionados si se solicita
        related_markers = None
        if payload.include_related:
            from sqlalchemy import select
            # Obtener otros resultados de la misma solicitud
            otros_detalles_stmt = select(detalle_solicitud_crud.model).where(
                detalle_solicitud_crud.model.id_solicitud == detalle.id_solicitud,
                detalle_solicitud_crud.model.id_detalle != detalle.id_detalle,
            )
            otros_detalles_result = await db.execute(otros_detalles_stmt)
            otros_detalles = otros_detalles_result.scalars().all()

            related_markers = []
            for otro_detalle in otros_detalles:
                otro_resultado_stmt = select(resultado_crud.model).where(
                    resultado_crud.model.id_detalle == otro_detalle.id_detalle
                )
                otro_resultado_result = await db.execute(otro_resultado_stmt)
                otro_resultado = otro_resultado_result.scalar_one_or_none()

                if otro_resultado:
                    otra_prueba = await prueba_crud.get(db, otro_detalle.id_prueba)
                    if otra_prueba:
                        related_markers.append({
                            "nombre": otra_prueba.nombre,
                            "valor": float(otro_resultado.resultado) if otro_resultado.resultado else 0,
                            "unidad": otra_prueba.unidad or "",
                            "estado": "anormal" if otro_resultado.es_anormal else "normal",
                        })

        # Realizar análisis
        analysis_result = await result_analyzer.analyze_result(
            patient_dict,
            result_dict,
            related_markers,
        )

        # Registrar evento
        audit_service.record_event("result_analysis", payload.patient_id, {
            "result_id": payload.result_id,
            "test_name": prueba.nombre,
            "include_related": payload.include_related,
        })

        return analysis_result

    except HTTPException:
        raise
    except Exception as exc:
        audit_service.record_event("result_analysis_error", payload.patient_id, {
            "error": str(exc)
        })
        raise HTTPException(status_code=500, detail=f"Error en análisis: {str(exc)}")

