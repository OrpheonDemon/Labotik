"""
Motor de Priorización - Clasifica urgencia clínica
"""

import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class PriorityEngine:
    """Motor de clasificación de urgencia clínica."""

    PRIORITY_LEVELS = {
        "CRÍTICO": {"orden": 1, "color": "#ff0000", "tiempo": "Inmediato"},
        "URGENTE": {"orden": 2, "color": "#ff6600", "tiempo": "1-2 horas"},
        "REVISIÓN": {"orden": 3, "color": "#ffcc00", "tiempo": "4-8 horas"},
        "NORMAL": {"orden": 4, "color": "#00cc00", "tiempo": "24-48 horas"}
    }

    def __init__(self, ollama_client):
        self.ollama_client = ollama_client

    async def prioritize(
        self,
        results: Dict[str, float],
        patient_age: int = None,
        critical_values: Dict[str, tuple] = None
    ) -> Dict[str, Any]:
        """Clasifica urgencia del análisis de resultados."""
        
        prompt = f"""Clasifica la urgencia clínica de estos resultados:

Resultados: {json.dumps(results, ensure_ascii=False)}
Edad: {patient_age or 'desconocida'} años
Valores críticos: {json.dumps(critical_values or {}, ensure_ascii=False)}

Clasifica como: CRÍTICO, URGENTE, REVISIÓN o NORMAL

Responde en JSON:
{{
    "prioridad": "CRÍTICO|URGENTE|REVISIÓN|NORMAL",
    "tiempo_respuesta": "Inmediato|1-2 horas|4-8 horas|24-48 horas",
    "razon": "explicacion breve",
    "valores_criticos": ["K=7.5", "Glu=650"],
    "notificar_medico": true,
    "confianza": 0.95
}}"""

        try:
            response = await self.ollama_client.generate_json(
                prompt=prompt,
                system="Eres especialista en triaje clínico. Prioriza según severidad.",
                temperature=0.2
            )
            
            # Validar estructura
            if "prioridad" not in response:
                response["prioridad"] = "REVISIÓN"
            if response["prioridad"] not in self.PRIORITY_LEVELS:
                response["prioridad"] = "REVISIÓN"
                
            return response
        except Exception as e:
            logger.error(f"Error prioritizing: {e}")
            return {
                "error": str(e),
                "prioridad": "REVISIÓN",
                "razon": "Error en análisis - requiere revisión humana"
            }

    async def calculate_risk_score(
        self,
        results: Dict[str, float]
    ) -> float:
        """Calcula score de riesgo del paciente (0-100)."""
        
        score = 0
        
        # Puntos por parámetro crítico
        if results.get("K", 0) > 7 or results.get("K", 0) < 2.5:
            score += 30
        elif results.get("K", 0) > 6 or results.get("K", 0) < 3:
            score += 15

        if results.get("Glu", 0) > 600:
            score += 25
        elif results.get("Glu", 0) < 40:
            score += 30

        if results.get("WBC", 0) > 25:
            score += 15
        
        if results.get("Hb", 0) < 5:
            score += 20

        # Máximo 100
        return min(score, 100)
