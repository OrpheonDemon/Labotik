"""
Detector de Anomalías - Identifica errores, hemólisis, lipemia y otros problemas
"""

import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Detector de anomalías en muestras y resultados."""

    def __init__(self, ollama_client):
        self.ollama_client = ollama_client

    async def detect_anomalies(
        self,
        results: Dict[str, float],
        reference_ranges: Dict[str, tuple] = None
    ) -> Dict[str, Any]:
        """Detecta anomalías, hemólisis, lipemia, errores de procesamiento."""
        
        prompt = f"""Analiza estos resultados buscando anomalías:

Resultados: {json.dumps(results, ensure_ascii=False)}
Rangos de referencia: {json.dumps(reference_ranges or {}, ensure_ascii=False)}

Detecta:
1. Hemólisis (K elevado + Hb baja)
2. Lipemia (triglicéridos muy altos)
3. Ictericia (bilirrubina elevada)
4. Valores críticos
5. Patrones inconsistentes

Responde en JSON:
{{
    "anomalias": ["hemolisis_probable", "valor_critico_K"],
    "severidad": "leve/moderada/severa",
    "acciones": ["rechazar_muestra", "recoletar", "revisar"],
    "urgencia": "INMEDIATO/URGENTE/REVISIÓN",
    "confianza": 0.9
}}"""

        try:
            response = await self.ollama_client.generate_json(
                prompt=prompt,
                system="Eres experto en control de calidad de laboratorio.",
                temperature=0.2
            )
            return response
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return {
                "error": str(e),
                "anomalias": [],
                "acciones": ["revisar_manualmente"]
            }

    async def validate_sample_quality(
        self,
        results: Dict[str, Any]
    ) -> List[str]:
        """Valida calidad de muestra basado en patrones clínicos."""
        
        issues = []

        # Hemólisis: K elevado + Hb baja
        if results.get("K", 0) > 5.5 and results.get("Hb", 20) < 10:
            issues.append("Posible hemólisis (K elevado con Hb baja)")

        # Lipemia: Triglicéridos > 400
        if results.get("TG", 0) > 400:
            issues.append("Muestra lipémica (triglicéridos muy elevados)")

        # Ictericia: Bilirrubina > 3
        if results.get("Bil", 0) > 3:
            issues.append("Muestra ictérica (bilirrubina muy elevada)")

        # Valores fuera de rango extremos
        if results.get("Glu", 0) > 600:
            issues.append("Glucosa crítica (>600 mg/dL)")

        if results.get("K", 0) > 7 or results.get("K", 0) < 2.5:
            issues.append("Potasio crítico - verificar muestra")

        return issues

    async def check_critical_values(
        self,
        results: Dict[str, float],
        critical_thresholds: Dict[str, tuple] = None
    ) -> Dict[str, Any]:
        """Identifica valores críticos que requieren notificación inmediata."""
        
        # Valores críticos por defecto
        defaults = {
            "Glu": (40, 600),
            "K": (2.5, 7),
            "Na": (120, 160),
            "Hb": (5, 20),
            "WBC": (2, 30),
            "Plt": (20, 1000),
            "Ca": (6, 13)
        }
        
        thresholds = critical_thresholds or defaults

        critical = []
        for param, value in results.items():
            if param in thresholds:
                low, high = thresholds[param]
                if value < low or value > high:
                    critical.append({
                        "parametro": param,
                        "valor": value,
                        "rango": f"{low}-{high}",
                        "tipo": "bajo" if value < low else "alto"
                    })

        return {
            "valores_criticos": critical,
            "requiere_notificacion": len(critical) > 0,
            "urgencia": "INMEDIATO" if critical else "NORMAL"
        }
