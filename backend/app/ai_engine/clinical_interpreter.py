import re
from typing import Any
from .ollama_client import OllamaClient
from .prompts import SYSTEM_PROMPT, ANALYSIS_PROMPT_TEMPLATE


class ClinicalInterpreter:
    def __init__(self, ollama_client: OllamaClient):
        self.client = ollama_client

    def build_laboratory_data(self, results: list[dict]) -> str:
        rows = []
        for item in results:
            rows.append(
                f"- {item.get('nombre')}:{' ' if item.get('resultado') else ''}{item.get('resultado', 'N/A')} {item.get('unidad','')} "
                f"(ref: {item.get('valor_referencia','N/A')}) {'ANORMAL' if item.get('es_anormal') else 'normal'}"
            )
        return "\n".join(rows)

    def build_prompt(self, results: list[dict], patient_context: str | None = None) -> str:
        patient_context = patient_context or "Sin contexto clínico adicional."
        laboratory_data = self.build_laboratory_data(results)
        return ANALYSIS_PROMPT_TEMPLATE.format(
            system_prompt=SYSTEM_PROMPT,
            patient_context=patient_context,
            laboratory_data=laboratory_data
        )

    async def interpret(self, results: list[dict], patient_context: str | None = None) -> dict[str, Any]:
        prompt = self.build_prompt(results, patient_context)
        raw_response = await self.client.generate(prompt)
        return self.parse_response(raw_response)

    def parse_response(self, raw_response: str) -> dict[str, Any]:
        sections = {
            'diagnostico_sugestivo': self._extract_section(raw_response, r'DIAGNÓSTICO SUGESTIVO:(.*?)(?=OBSERVACIONES:|ANOMALÍAS Y ERRORES:|PRIORIDAD:|RECOMENDACIONES:|VALIDACIÓN HUMANA:|$)'),
            'observaciones': self._extract_list(raw_response, r'OBSERVACIONES:(.*?)(?=ANOMALÍAS Y ERRORES:|PRIORIDAD:|RECOMENDACIONES:|VALIDACIÓN HUMANA:|$)'),
            'anomalies': self._extract_list(raw_response, r'ANOMALÍAS Y ERRORES:(.*?)(?=PRIORIDAD:|RECOMENDACIONES:|VALIDACIÓN HUMANA:|$)'),
            'prioridad': self._extract_section(raw_response, r'PRIORIDAD:(.*?)(?=RECOMENDACIONES:|VALIDACIÓN HUMANA:|$)'),
            'recomendaciones': self._extract_section(raw_response, r'RECOMENDACIONES:(.*?)(?=VALIDACIÓN HUMANA:|$)'),
            'validacion_humana': self._extract_section(raw_response, r'VALIDACIÓN HUMANA:(.*)$'),
        }
        return sections

    def _extract_section(self, text: str, pattern: str) -> str:
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else ""

    def _extract_list(self, text: str, pattern: str) -> list[str]:
        raw = self._extract_section(text, pattern)
        if not raw:
            return []
        return [line.strip('-* \t') for line in raw.splitlines() if line.strip()]
