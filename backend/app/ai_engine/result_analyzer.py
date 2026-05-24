"""
Analizador específico de resultados con MedGEMMA.
Proporciona análisis detallado de resultados individuales de laboratorio.
"""

import json
import logging
from typing import Any, Optional
from datetime import datetime
from .ollama_client import OllamaClient
from .prompts import RESULT_ANALYSIS_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


class ResultAnalyzer:
    """
    Realiza análisis clínico específico de resultados laboratoriales.
    Interpreta valores, correlaciona biomarcadores y proporciona recomendaciones.
    """

    def __init__(self, ollama_client: OllamaClient):
        self.client = ollama_client

    async def analyze_result(
        self,
        patient_data: dict[str, Any],
        result_data: dict[str, Any],
        related_markers: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        """
        Analiza un resultado específico de laboratorio.

        Args:
            patient_data: Información del paciente
            result_data: Datos del resultado (prueba, valor, referencia, etc.)
            related_markers: Otros biomarcadores relacionados

        Returns:
            Análisis específico del resultado
        """
        # Obtener información del resultado
        test_value = result_data.get("valor", 0)
        reference_low = result_data.get("rango_min", 0)
        reference_high = result_data.get("rango_max", 100)

        # Calcular desviación
        if test_value > reference_high:
            deviation = ((test_value - reference_high) / reference_high) * 100
        elif test_value < reference_low:
            deviation = ((reference_low - test_value) / reference_low) * 100
        else:
            deviation = 0

        # Construir contexto de biomarcadores relacionados
        related_text = self._format_related_markers(related_markers or [])

        # Construir el prompt
        prompt = RESULT_ANALYSIS_PROMPT_TEMPLATE.format(
            system_prompt="",
            patient_name=patient_data.get("nombre", "No especificado"),
            patient_age=self._calculate_age(patient_data.get("fecha_nacimiento")),
            patient_gender=self._translate_gender(patient_data.get("genero")),
            test_name=result_data.get("nombre_prueba", "Desconocida"),
            test_result=result_data.get("valor", "N/A"),
            reference_range=f"{reference_low}-{reference_high}",
            unit=result_data.get("unidad", ""),
            test_value=test_value,
            reference_low=reference_low,
            reference_high=reference_high,
            deviation_percentage=abs(round(deviation, 1)),
            clinical_context=result_data.get("contexto_clinico", "No especificado"),
            related_markers=related_text,
        )

        try:
            response = await self.client.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=1500,
            )

            # Parsear respuesta JSON
            analysis = self._parse_json_response(response)

            return {
                "status": "success",
                "patient_id": patient_data.get("id_paciente"),
                "result_id": result_data.get("id_resultado"),
                "test_name": result_data.get("nombre_prueba"),
                "analysis_timestamp": datetime.now().isoformat(),
                "analysis": analysis,
                "raw_response": response,
            }

        except Exception as exc:
            logger.error(f"Error analizando resultado: {exc}")
            return {
                "status": "error",
                "patient_id": patient_data.get("id_paciente"),
                "result_id": result_data.get("id_resultado"),
                "error": str(exc),
            }

    def _format_related_markers(self, markers: list[dict[str, Any]]) -> str:
        """Formatea biomarcadores relacionados para el prompt."""
        if not markers:
            return "No hay biomarcadores relacionados disponibles."

        formatted = []
        for marker in markers:
            name = marker.get("nombre", "Desconocido")
            value = marker.get("valor", "N/A")
            unit = marker.get("unidad", "")
            status = marker.get("estado", "Normal")

            formatted.append(f"- {name}: {value} {unit} [{status}]")

        return "\n".join(formatted) if formatted else "Sin biomarcadores relacionados."

    def _calculate_age(self, birth_date: Optional[Any]) -> int:
        """Calcula la edad a partir de la fecha de nacimiento."""
        if not birth_date:
            return 0

        try:
            from datetime import date
            if isinstance(birth_date, str):
                birth_date = datetime.fromisoformat(birth_date.split()[0]).date()
            elif hasattr(birth_date, 'date'):
                birth_date = birth_date.date()

            today = date.today()
            return today.year - birth_date.year - (
                (today.month, today.day) < (birth_date.month, birth_date.day)
            )
        except Exception:
            return 0

    def _translate_gender(self, gender: Optional[str]) -> str:
        """Traduce código de género a texto legible."""
        gender_map = {
            'M': 'Masculino',
            'F': 'Femenino',
            'O': 'Otro'
        }
        return gender_map.get(gender, 'No especificado')

    def _parse_json_response(self, response: str) -> dict[str, Any]:
        """Intenta parsear la respuesta JSON del modelo."""
        try:
            # Intentar parsear directamente
            return json.loads(response)
        except json.JSONDecodeError:
            # Si falla, buscar un JSON dentro de la respuesta
            try:
                import re
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except Exception:
                pass

            # Si todo falla, retornar estructura por defecto
            return {
                "resultado_interpretacion": "Análisis no disponible",
                "significado_clinico": "Requiere revisión manual",
                "severidad": "moderada",
                "causas_posibles": ["Requiere evaluación clínica"],
                "patologias_sugestivas": [],
                "correlacion_con_biomarcadores": [],
                "posibles_errores_preanaliticos": [],
                "recomendaciones_seguimiento": ["Validación médica requerida"],
                "urgencia": "pronto",
                "requiere_medico": True,
                "interpretacion_completa": "Respuesta del modelo requiere validación profesional",
            }
