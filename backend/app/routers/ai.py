"""
Router de IA Clínica - Endpoints para análisis inteligentes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.database import get_db
from app.dependencies import require_medico, require_admin, get_current_active_user
from app.ai_engine import (
    OllamaClient,
    ClinicalInterpreter,
    AnomalyDetector,
    PriorityEngine,
    ClinicalAssistant,
    AuditService
)

router = APIRouter(
    prefix="/ai",
    tags=["IA Clínica"]
)

# Instancias globales
ollama_client = None
audit_service = AuditService()


async def get_ollama_client():
    """Factory para obtener cliente de Ollama."""
    global ollama_client
    if ollama_client is None:
        ollama_client = OllamaClient()
    return ollama_client


@router.get("/status")
async def ai_status():
    """Verifica el estado del motor IA y Ollama."""
    try:
        client = OllamaClient()
        is_available = await client.check_status()
        
        return {
            "status": "available" if is_available else "unavailable",
            "ollama_running": is_available,
            "models": ["medgemma:latest"] if is_available else [],
            "model_active": is_available,
            "message": "Motor IA operativo" if is_available else "Ollama no disponible en localhost:11434"
        }
    except Exception as e:
        return {
            "status": "error",
            "ollama_running": False,
            "message": f"Error: {str(e)}"
        }


@router.post("/interpret-results")
async def interpret_results(
    request: Dict[str, Any],
    current_user: dict = Depends(require_medico),
    db: AsyncSession = Depends(get_db)
):
    """Interpreta resultados de laboratorio usando IA."""
    
    try:
        client = await get_ollama_client()
        if not await client.check_status():
            raise HTTPException(
                status_code=503,
                detail="Motor IA no disponible. Verifica que Ollama esté corriendo en puerto 11434"
            )

        interpreter = ClinicalInterpreter(client)
        
        interpretation = await interpreter.interpret_results(
            results=request.get("resultados", {}),
            patient_age=request.get("edad"),
            patient_gender=request.get("sexo"),
            clinical_history=request.get("historial_clinico")
        )

        # Registrar en auditoría
        audit_service.log_analysis(
            analysis_type="interpretacion",
            user_email=current_user["user"].email,
            patient_id=request.get("id_paciente", "unknown"),
            input_data=request,
            ai_output=interpretation,
            confidence=interpretation.get("confianza", 0.8)
        )

        return {
            "status": "success",
            "interpretation": interpretation
        }
    except HTTPException:
        raise
    except Exception as e:
        return {
            "status": "error",
            "detail": str(e)
        }


@router.post("/detect-anomalies")
async def detect_anomalies(
    request: Dict[str, Any],
    current_user: dict = Depends(require_medico),
    db: AsyncSession = Depends(get_db)
):
    """Detecta anomalías en muestras (hemólisis, lipemia, etc)."""
    
    try:
        client = await get_ollama_client()
        if not await client.check_status():
            raise HTTPException(status_code=503, detail="Motor IA no disponible")

        detector = AnomalyDetector(client)
        
        anomalies = await detector.detect_anomalies(
            results=request.get("resultados", {}),
            reference_ranges=request.get("rangos_referencia")
        )

        audit_service.log_analysis(
            analysis_type="deteccion_anomalias",
            user_email=current_user["user"].email,
            patient_id=request.get("id_paciente", "unknown"),
            input_data=request,
            ai_output=anomalies,
            confidence=anomalies.get("confianza", 0.8)
        )

        return {
            "status": "success",
            "anomalies": anomalies
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.post("/prioritize")
async def prioritize(
    request: Dict[str, Any],
    current_user: dict = Depends(require_medico),
    db: AsyncSession = Depends(get_db)
):
    """Clasifica urgencia clínica de los resultados."""
    
    try:
        client = await get_ollama_client()
        if not await client.check_status():
            raise HTTPException(status_code=503, detail="Motor IA no disponible")

        priority_engine = PriorityEngine(client)
        
        priority = await priority_engine.prioritize(
            results=request.get("resultados", {}),
            patient_age=request.get("edad"),
            critical_values=request.get("valores_criticos")
        )

        audit_service.log_analysis(
            analysis_type="priorizacion",
            user_email=current_user["user"].email,
            patient_id=request.get("id_paciente", "unknown"),
            input_data=request,
            ai_output=priority,
            confidence=priority.get("confianza", 0.9)
        )

        return {
            "status": "success",
            "priority": priority
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.post("/chat")
async def chat(
    request: Dict[str, Any],
    current_user: dict = Depends(require_medico)
):
    """Chat clínico interactivo para consultas sobre resultados."""
    
    try:
        client = await get_ollama_client()
        if not await client.check_status():
            raise HTTPException(status_code=503, detail="Motor IA no disponible")

        assistant = ClinicalAssistant(client)
        
        response = await assistant.ask_question(
            question=request.get("pregunta", ""),
            patient_age=request.get("edad"),
            patient_gender=request.get("sexo"),
            test_name=request.get("nombre_prueba"),
            test_value=request.get("valor"),
            reference_range=request.get("rango_referencia")
        )

        return {
            "status": "success",
            "respuesta": response
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.post("/explain-biomarker")
async def explain_biomarker(
    request: Dict[str, Any],
    current_user: dict = Depends(require_medico)
):
    """Explica qué significa un biomarcador específico."""
    
    try:
        client = await get_ollama_client()
        if not await client.check_status():
            raise HTTPException(status_code=503, detail="Motor IA no disponible")

        assistant = ClinicalAssistant(client)
        
        explanation = await assistant.explain_biomarker(
            biomarker_name=request.get("biomarcador", ""),
            value=request.get("valor", 0),
            reference_range=request.get("rango_referencia", ""),
            patient_context=request.get("contexto")
        )

        return {
            "status": "success",
            "explicacion": explanation
        }
    except HTTPException:
        raise
    except Exception as e:
        return {"status": "error", "detail": str(e)}


@router.get("/audit-log")
async def get_audit_log(
    current_user: dict = Depends(require_admin),
    limit: int = 50,
    tipo: str = None
):
    """Obtiene registro de auditoría de análisis de IA (solo admin)."""
    
    logs = audit_service.get_audit_logs(limit=limit, analysis_type=tipo)
    stats = audit_service.get_statistics()
    
    return {
        "status": "success",
        "registros": logs,
        "estadisticas": stats
    }


@router.get("/health")
async def health_check():
    """Verifica el estado del motor IA y sus componentes."""
    
    try:
        from app.ai_engine import OllamaClient
        from app.ai_engine.reference_ranges import get_reference_range
        from app.ai_engine.medical_prompts import get_system_prompt_names
        
        # Test Ollama
        client = OllamaClient()
        ollama_status = await client.check_status()
        
        # Test módulos
        modules_ok = True
        errors = []
        
        try:
            ranges = get_reference_range("hemoglobina")
            if not ranges:
                errors.append("reference_ranges: fallo")
                modules_ok = False
        except Exception as e:
            errors.append(f"reference_ranges: {str(e)}")
            modules_ok = False
        
        try:
            prompts = get_system_prompt_names()
            if len(prompts) < 9:
                errors.append(f"medical_prompts: solo {len(prompts)}/9 prompts")
                modules_ok = False
        except Exception as e:
            errors.append(f"medical_prompts: {str(e)}")
            modules_ok = False
        
        return {
            "status": "healthy" if ollama_status and modules_ok else "degraded",
            "components": {
                "ollama": "available" if ollama_status else "unavailable",
                "modules": "ok" if modules_ok else "error",
                "audit_service": "available"
            },
            "errors": errors if errors else [],
            "timestamp": str(__import__('datetime').datetime.now())
        }
    
    except Exception as e:
        return {
            "status": "error",
            "detail": str(e),
            "errors": [str(e)]
        }


@router.post("/specialized-analysis")
async def specialized_analysis(
    request: Dict[str, Any],
    current_user: dict = Depends(require_medico),
    db: AsyncSession = Depends(get_db)
):
    """
    Realiza análisis especializado según disciplina médica.
    
    Request:
    {
        "specialty": "hematology|biochemistry|coagulation|endocrinology|immunology|microbiology",
        "resultados": {...},
        "paciente": {
            "edad": int,
            "sexo": "hombre|mujer",
            "antecedentes": str
        }
    }
    """
    
    try:
        from app.ai_engine.specialized_analyzers import run_specialized_analysis
        
        specialty = request.get("specialty", "").lower()
        results = request.get("resultados", {})
        patient_info = request.get("paciente", {})
        
        if not specialty:
            raise HTTPException(
                status_code=400,
                detail="Se requiere especificar 'specialty': hematology, biochemistry, coagulation, endocrinology, immunology, microbiology"
            )
        
        # Ejecutar análisis especializado
        analysis_result = await run_specialized_analysis(specialty, results, patient_info)
        
        if analysis_result is None:
            raise HTTPException(
                status_code=400,
                detail=f"Especialidad '{specialty}' no válida"
            )
        
        # Registrar en auditoría
        audit_service.log_analysis(
            analysis_type=f"specialized_{specialty}",
            user_email=current_user["user"].email,
            patient_id=request.get("id_paciente", "unknown"),
            input_data=request,
            ai_output=analysis_result.to_dict(),
            confidence=0.85
        )
        
        return {
            "status": "success",
            "analysis": analysis_result.to_dict()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        return {
            "status": "error",
            "detail": str(e)
        }


@router.get("/models")
async def list_models():
    """Lista modelos de IA disponibles en Ollama."""
    
    try:
        client = OllamaClient()
        
        # Verificar disponibilidad
        is_available = await client.check_status()
        
        if not is_available:
            return {
                "status": "unavailable",
                "models": [],
                "message": "Ollama no disponible en localhost:11434"
            }
        
        # Modelos recomendados para laboratorio clínico
        recommended_models = [
            {
                "name": "medgemma",
                "full_name": "medgemma:latest",
                "size": "7B",
                "specialty": "Medicina general y análisis clínico",
                "installed": True  # Asumimos instalado si Ollama responde
            },
            {
                "name": "neural-chat",
                "full_name": "neural-chat:latest",
                "size": "7B",
                "specialty": "Chat general (respaldo)",
                "installed": False
            }
        ]
        
        return {
            "status": "success",
            "available": True,
            "models": recommended_models,
            "current_model": "medgemma:latest",
            "instructions": {
                "install": "ollama pull medgemma",
                "run_server": "ollama serve",
                "endpoint": "http://localhost:11434"
            }
        }
    
    except Exception as e:
        return {
            "status": "error",
            "detail": str(e),
            "available": False
        }


@router.post("/validate-results")
async def validate_results(
    request: Dict[str, Any],
    current_user: dict = Depends(require_medico),
    db: AsyncSession = Depends(get_db)
):
    """
    Valida resultados de laboratorio contra rangos de referencia.
    
    Retorna: valores fuera de rango, valores críticos, alertas
    """
    
    try:
        from app.ai_engine.reference_ranges import (
            get_reference_range,
            is_critical,
            get_interpretation_level
        )
        
        results = request.get("resultados", {})
        patient_info = request.get("paciente", {})
        
        validation = {
            "normal": [],
            "out_of_range": [],
            "critical": [],
            "unknown": []
        }
        
        for test_name, value in results.items():
            range_info = get_reference_range(
                test_name,
                age=patient_info.get("edad"),
                gender=patient_info.get("sexo")
            )
            
            if range_info:
                level = get_interpretation_level(test_name, value)
                
                if is_critical(test_name, value):
                    validation["critical"].append({
                        "test": test_name,
                        "value": value,
                        "level": level,
                        "range": f"{range_info.get('min')}-{range_info.get('max')} {range_info.get('unidad')}"
                    })
                elif level != "NORMAL":
                    validation["out_of_range"].append({
                        "test": test_name,
                        "value": value,
                        "level": level,
                        "range": f"{range_info.get('min')}-{range_info.get('max')} {range_info.get('unidad')}"
                    })
                else:
                    validation["normal"].append({
                        "test": test_name,
                        "value": value,
                        "level": "NORMAL",
                        "range": f"{range_info.get('min')}-{range_info.get('max')} {range_info.get('unidad')}"
                    })
            else:
                validation["unknown"].append({
                    "test": test_name,
                    "value": value,
                    "reason": "Prueba no encontrada en base de datos de rangos"
                })
        
        return {
            "status": "success",
            "validation": validation,
            "summary": {
                "total": len(results),
                "normal": len(validation["normal"]),
                "out_of_range": len(validation["out_of_range"]),
                "critical": len(validation["critical"]),
                "unknown": len(validation["unknown"])
            }
        }
    
    except Exception as e:
        return {
            "status": "error",
            "detail": str(e)
        }
