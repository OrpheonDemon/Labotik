"""
Intérprete Clínico - Análisis de resultados de laboratorio
"""

import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)


class ClinicalInterpreter:
    """Intérprete de resultados clínicos con análisis especializados."""

    def __init__(self, ollama_client):
        self.ollama_client = ollama_client

    async def interpret_results(
        self,
        results: Dict[str, Any],
        patient_age: Optional[int] = None,
        patient_gender: Optional[str] = None,
        clinical_history: Optional[str] = None
    ) -> Dict[str, Any]:
        """Interpreta resultados generales de laboratorio."""
        
        prompt = f"""Analiza estos resultados de laboratorio de forma clínica:

Resultados: {json.dumps(results, ensure_ascii=False)}
Edad paciente: {patient_age or 'No especificada'} años
Sexo: {patient_gender or 'No especificado'}
Historial clínico: {clinical_history or 'No disponible'}

Por favor proporciona:
1. Hallazgos relevantes
2. Interpretación clínica
3. Alertas críticas (si las hay)
4. Prioridad (CRÍTICO, URGENTE, REVISIÓN, NORMAL)
5. Recomendaciones

Responde en JSON con estructura:
{{
    "hallazgos": ["hallazgo1", "hallazgo2"],
    "interpretacion": "texto",
    "alertas": ["alerta1"],
    "prioridad": "REVISIÓN",
    "confianza": 0.85,
    "requiere_revision_humana": true,
    "recomendaciones": ["recomendacion1"]
}}"""

        try:
            response = await self.ollama_client.generate_json(
                prompt=prompt,
                system="Eres un patólogo clínico experto. Analiza solo, no diagnostiques.",
                temperature=0.3
            )
            
            # Validar estructura mínima
            if "hallazgos" not in response:
                response["hallazgos"] = []
            if "prioridad" not in response:
                response["prioridad"] = "REVISIÓN"
            response["requiere_revision_humana"] = True
            
            return response
        except Exception as e:
            logger.error(f"Error interpreting results: {e}")
            return {
                "error": str(e),
                "hallazgos": [],
                "prioridad": "REVISIÓN",
                "requiere_revision_humana": True
            }

    async def analyze_anemia(
        self,
        hemoglobin: Optional[float] = None,
        hematocrit: Optional[float] = None,
        rbc: Optional[float] = None,
        mcv: Optional[float] = None,
        iron_studies: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Análisis especializado de anemia."""
        
        data = {
            "hemoglobina": hemoglobin,
            "hematocrito": hematocrit,
            "rbcs": rbc,
            "vcm": mcv
        }
        if iron_studies:
            data.update(iron_studies)

        prompt = f"""Análisis de posible anemia con estos datos:
{json.dumps(data, ensure_ascii=False)}

Clasifica tipo y severidad. Responde en JSON:
{{
    "diagnostico": "anemia leve/moderada/severa" o "normal",
    "tipo": "normocitica/microcitica/macrocitica/mixta",
    "causa_probable": "perdida/hemolisis/deficiencia/mixta",
    "recomendaciones": ["estudios_adicionales"],
    "confianza": 0.8
}}"""

        try:
            return await self.ollama_client.generate_json(prompt=prompt, temperature=0.3)
        except Exception as e:
            logger.error(f"Error in anemia analysis: {e}")
            return {"error": str(e), "diagnostico": "desconocido"}

    async def analyze_inflammation(
        self,
        crp: Optional[float] = None,
        wbc: Optional[float] = None,
        esr: Optional[float] = None,
        procalcitonin: Optional[float] = None
    ) -> Dict[str, Any]:
        """Análisis de inflamación/infección."""
        
        data = {
            "pcr": crp,
            "leucocitos": wbc,
            "esr": esr,
            "procalcitonina": procalcitonin
        }

        prompt = f"""Análisis de marcadores inflamatorios:
{json.dumps(data, ensure_ascii=False)}

Determina si hay inflamación/infección. JSON:
{{
    "hay_inflamacion": true/false,
    "severidad": "leve/moderada/severa",
    "tipo_probable": "bacteriana/viral/aseptica/otra",
    "urgencia": "CRÍTICO/URGENTE/REVISIÓN",
    "recomendaciones": ["antibioticos_considerar", "cultivos"]
}}"""

        try:
            return await self.ollama_client.generate_json(prompt=prompt, temperature=0.3)
        except Exception as e:
            logger.error(f"Error in inflammation analysis: {e}")
            return {"error": str(e)}

    async def analyze_renal_function(
        self,
        creatinine: Optional[float] = None,
        bun: Optional[float] = None,
        gfr: Optional[float] = None
    ) -> Dict[str, Any]:
        """Análisis de función renal."""
        
        data = {"creatinina": creatinine, "urea": bun, "fge": gfr}

        prompt = f"""Análisis de función renal:
{json.dumps(data, ensure_ascii=False)}

Responde:
{{
    "funcion_renal": "normal/leve/moderada/severa",
    "estadio_ckd": 1-5 o "normal",
    "recomendaciones": [],
    "urgencia": "REVISIÓN"
}}"""

        try:
            return await self.ollama_client.generate_json(prompt=prompt, temperature=0.3)
        except Exception as e:
            logger.error(f"Error in renal analysis: {e}")
            return {"error": str(e)}

    async def analyze_hepatic_function(
        self,
        alt: Optional[float] = None,
        ast: Optional[float] = None,
        bilirubin: Optional[float] = None,
        albumin: Optional[float] = None
    ) -> Dict[str, Any]:
        """Análisis de función hepática."""
        
        data = {"alt": alt, "ast": ast, "bilirrubina": bilirubin, "albumina": albumin}

        prompt = f"""Análisis de función hepática:
{json.dumps(data, ensure_ascii=False)}

Responde:
{{
    "funcion_hepatica": "normal/alterada",
    "patron": "hepatitico/colestasico/mixto",
    "severidad": "leve/moderada/severa",
    "recomendaciones": ["estudios", "seguimiento"]
}}"""

        try:
            return await self.ollama_client.generate_json(prompt=prompt, temperature=0.3)
        except Exception as e:
            logger.error(f"Error in hepatic analysis: {e}")
            return {"error": str(e)}
