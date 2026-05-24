"""
Analizador integral de pacientes con MedGEMMA.
Proporciona análisis completo del estado general del paciente.
"""

import json
import logging
from typing import Any, Optional
from datetime import datetime
from .ollama_client import OllamaClient
from .prompts import PATIENT_ANALYSIS_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


class PatientAnalyzer:
    """
    Realiza análisis clínico integral de pacientes.
    Analiza historiales, patrones y correlaciones médicas.
    """

    def __init__(self, ollama_client: OllamaClient):
        self.client = ollama_client

    async def analyze_patient(
        self,
        patient_data: dict[str, Any],
        medical_history: Optional[list[dict[str, Any]]] = None,
        recent_results: Optional[list[dict[str, Any]]] = None,
    ) -> dict[str, Any]:
        """
        Analiza integralmente el perfil de un paciente.

        Args:
            patient_data: Información del paciente (nombre, edad, género, etc.)
            medical_history: Histórico de resultados previos
            recent_results: Resultados recientes de laboratorio

        Returns:
            Análisis integral del paciente
        """
        # Construir contexto de historial médico
        medical_history_text = self._format_medical_history(medical_history or [])

        # Construir contexto de resultados recientes
        recent_results_text = self._format_recent_results(recent_results or [])

        # Construir el prompt
        prompt = PATIENT_ANALYSIS_PROMPT_TEMPLATE.format(
            system_prompt="",
            patient_name=patient_data.get("nombre", "No especificado"),
            patient_age=self._calculate_age(patient_data.get("fecha_nacimiento")),
            patient_gender=self._translate_gender(patient_data.get("genero")),
            patient_blood_type=patient_data.get("tipo_sangre", "No especificado"),
            patient_allergies=patient_data.get("alergias", "No registradas") or "No registradas",
            last_visit_date="No disponible",
            medical_history=medical_history_text,
            recent_results=recent_results_text,
        )

        try:
            response = await self.client.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=1200,
            )

            # Parsear respuesta JSON
            analysis = self._parse_json_response(response)

            return {
                "status": "success",
                "patient_id": patient_data.get("id_paciente"),
                "analysis_timestamp": datetime.now().isoformat(),
                "analysis": analysis,
                "raw_response": response,
            }

        except Exception as exc:
            logger.error(f"Error analizando paciente: {exc}")
            return {
                "status": "error",
                "patient_id": patient_data.get("id_paciente"),
                "error": str(exc),
            }

    def _format_medical_history(self, history: list[dict[str, Any]]) -> str:
        """Formatea el histórico médico para el prompt."""
        if not history:
            return "No hay datos históricos previos disponibles."

        formatted = []
        for record in history[-5:]:  # Últimos 5 registros
            date = record.get("fecha", "Desconocida")
            findings = record.get("hallazgos", "Sin datos")
            priority = record.get("prioridad", "Desconocida")
            formatted.append(
                f"- {date}: {findings} (Prioridad: {priority})"
            )

        return "\n".join(formatted) if formatted else "Historial vacío."

    def _format_recent_results(self, results: list[dict[str, Any]]) -> str:
        """Formatea los resultados recientes para el prompt."""
        if not results:
            return "No hay resultados recientes disponibles."

        formatted = []
        for result in results:
            test_name = result.get("nombre_prueba", "Desconocida")
            value = result.get("valor", "N/A")
            unit = result.get("unidad", "")
            reference = result.get("rango_referencia", "N/A")
            status = result.get("estado", "No especificado")

            formatted.append(
                f"- {test_name}: {value} {unit} (Rango: {reference}) [{status}]"
            )

        return "\n".join(formatted) if formatted else "Sin resultados."

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
                "perfil_general_paciente": "Análisis no disponible",
                "hallazgos_integrales": ["Requiere revisión manual"],
                "patrones_detectados": [],
                "correlaciones_importantes": [],
                "alertas_seguimiento": [],
                "prioridad_seguimiento": "media",
                "recomendaciones_clinicas": [],
                "proximos_estudios_sugeridos": [],
                "requiere_revision_medico": True,
                "notas_seguridad": "Respuesta del modelo requiere validación",
            }
