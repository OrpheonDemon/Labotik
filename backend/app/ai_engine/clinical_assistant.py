"""
Asistente Clínico - Chat interactivo y análisis contextual
"""

import json
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ClinicalAssistant:
    """Asistente clínico interactivo para consultas y análisis."""

    def __init__(self, ollama_client):
        self.ollama_client = ollama_client

    async def ask_question(
        self,
        question: str,
        patient_age: int = None,
        patient_gender: str = None,
        test_name: str = None,
        test_value: float = None,
        reference_range: str = None
    ) -> str:
        """Responde preguntas clínicas sobre resultados específicos."""
        
        context = f"""
Paciente: {patient_age} años, {patient_gender or 'sexo no especificado'}
Prueba: {test_name or 'desconocida'} = {test_value or 'valor no especificado'}
Rango normal: {reference_range or 'no especificado'}

Pregunta: {question}"""

        prompt = f"""Responde esta pregunta clínica de forma clara y educativa:

{context}

Normas:
- Explica en lenguaje médico pero comprensible
- No diagnostiques, solo explica
- Sugiere cuando se necesite revisión médica
- Mantén respuesta concisa (máximo 5 líneas)"""

        try:
            response = await self.ollama_client.generate_text(
                prompt=prompt,
                system="Eres un asistente clínico educativo. Explica de forma profesional pero clara.",
                temperature=0.4
            )
            return response
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return "Lo siento, no puedo procesar tu pregunta en este momento. Por favor consulta con tu médico."

    async def compare_with_history(
        self,
        current_results: Dict[str, float],
        previous_results: List[Dict[str, float]]
    ) -> Dict[str, Any]:
        """Compara resultados actuales con histórico del paciente."""
        
        if not previous_results:
            return {"comparacion": "Sin histórico previo", "tendencia": "N/A"}

        prompt = f"""Compara estos resultados con el histórico:

Actual: {json.dumps(current_results, ensure_ascii=False)}
Histórico: {json.dumps(previous_results, ensure_ascii=False)}

Analiza:
1. Tendencia (mejorando/empeorando/estable)
2. Cambios significativos
3. Recomendaciones

Responde en JSON:
{{
    "tendencia": "mejorando|empeorando|estable",
    "cambios_significativos": ["parametro1 empeorando", "parametro2 normalizado"],
    "interpretacion": "texto breve",
    "recomendaciones": ["seguimiento en X días"]
}}"""

        try:
            return await self.ollama_client.generate_json(
                prompt=prompt,
                system="Eres especialista en seguimiento clínico.",
                temperature=0.3
            )
        except Exception as e:
            logger.error(f"Error comparing history: {e}")
            return {"error": str(e), "tendencia": "desconocida"}

    async def explain_biomarker(
        self,
        biomarker_name: str,
        value: float,
        reference_range: str,
        patient_context: str = None
    ) -> str:
        """Explica qué significa un biomarcador específico."""
        
        prompt = f"""Explica este biomarcador de forma educativa:

Biomarcador: {biomarker_name}
Valor del paciente: {value}
Rango normal: {reference_range}
Contexto: {patient_context or 'desconocido'}

Responde:
1. ¿Qué es este biomarcador?
2. ¿Qué significa el valor del paciente?
3. ¿Cuándo se preocupa el médico?
4. Mantén respuesta corta (máximo 6 líneas)"""

        try:
            response = await self.ollama_client.generate_text(
                prompt=prompt,
                system="Eres un educador clínico. Explica de forma clara y no alarmista.",
                temperature=0.3
            )
            return response
        except Exception as e:
            logger.error(f"Error explaining biomarker: {e}")
            return "No puedo explicar este biomarcador ahora. Consulta a tu médico."

    async def generate_patient_summary(
        self,
        patient_data: Dict[str, Any],
        recent_results: Dict[str, float]
    ) -> str:
        """Genera resumen clínico del paciente."""
        
        prompt = f"""Genera un resumen clínico BREVE del paciente:

Datos: {json.dumps(patient_data, ensure_ascii=False)}
Resultados recientes: {json.dumps(recent_results, ensure_ascii=False)}

Formato:
- Impresión general (1-2 líneas)
- Hallazgos principales (máximo 3)
- Recomendación (1 línea)

Máximo 5 líneas total."""

        try:
            response = await self.ollama_client.generate_text(
                prompt=prompt,
                system="Eres un clínico conciso. Resume solo lo importante.",
                temperature=0.3
            )
            return response
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return "Resumen no disponible"
