import aiohttp
import logging
import asyncio
import re
from typing import Tuple, Dict, Any
from app.ai_engine.prompts import SYSTEM_PROMPT, ANALYSIS_PROMPT_TEMPLATE

logger = logging.getLogger(__name__)


class OllamaService:
    """Servicio para comunicarse con Ollama y usar MedGemma como motor IA."""

    def __init__(self, model: str = "medgemma", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api"
        self.session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def verificar_conexion(self) -> bool:
        try:
            session = await self._get_session()
            async with session.get(f"{self.api_url}/models", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                return resp.status == 200
        except Exception as exc:
            logger.error(f"Error verificando conexión a Ollama: {exc}")
            return False

    async def analizar_resultados(
        self,
        datos_clinicos: Dict[str, Any],
        id_paciente: str
    ) -> Tuple[str, float, Dict[str, Any], Dict[str, Any], str]:
        prompt = self._construir_prompt(datos_clinicos, id_paciente)
        raw_response = await self._llamar_ollama(prompt)

        diagnostico_actual, confianza = self._extraer_diagnostico_actual(raw_response)
        predicciones = self._extraer_predicciones(raw_response)
        factores_riesgo = self._extraer_factores_riesgo(raw_response)
        recomendaciones = self._extraer_recomendaciones(raw_response)

        if not recomendaciones:
            recomendaciones = "Consulte con su médico para validación clínica final."

        return diagnostico_actual, confianza, predicciones, factores_riesgo, recomendaciones

    async def _llamar_ollama(self, prompt: str) -> str:
        session = await self._get_session()
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": 0.2,
            "max_tokens": 800,
            "stream": False
        }

        try:
            async with session.post(
                f"{self.api_url}/generate",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as resp:
                text = await resp.text()
                if resp.status != 200:
                    logger.error(f"Ollama API error {resp.status}: {text}")
                    raise Exception(f"Ollama API error: {resp.status}")
                data = await resp.json()
                return data.get("response", data.get("text", "")).strip()
        except asyncio.TimeoutError:
            raise Exception("Timeout esperando respuesta de Ollama")
        except Exception as exc:
            logger.error(f"Error llamando a Ollama: {exc}")
            raise

    def _construir_prompt(self, datos_clinicos: Dict[str, Any], id_paciente: str) -> str:
        pruebas_text = "\n".join([
            f"- {p.get('nombre')}: {p.get('resultado')} {p.get('unidad')} (ref: {p.get('valor_referencia')}) {'⚠️ ANORMAL' if p.get('es_anormal') else '✓'}"
            for p in datos_clinicos.get("pruebas", [])
        ])

        return ANALYSIS_PROMPT_TEMPLATE.format(
            system_prompt=SYSTEM_PROMPT,
            patient_context=f"Paciente ID: {id_paciente}. Contexto clínico base generado desde el LIS.",
            laboratory_data=pruebas_text
        )

    def _extraer_diagnostico_actual(self, respuesta: str) -> Tuple[str, float]:
        diagnostico_match = re.search(
            r'DIAGNÓSTICO SUGESTIVO:\s*\n(.*?)(?=OBSERVACIONES:|ANOMALÍAS Y ERRORES:|PRIORIDAD:|RECOMENDACIONES:|VALIDACIÓN HUMANA:|$)',
            respuesta,
            re.DOTALL | re.IGNORECASE
        )
        diagnostico = diagnostico_match.group(1).strip() if diagnostico_match else "Hallazgos clínicos en proceso de evaluación."

        confianza_match = re.search(r'SCORE:\s*(\d+)', respuesta, re.IGNORECASE)
        confianza = float(confianza_match.group(1)) / 100 if confianza_match else 0.5

        return diagnostico, min(1.0, max(0.0, confianza))

    def _extraer_predicciones(self, respuesta: str) -> Dict[str, Any]:
        match = re.search(r'PRIORIDAD:\s*(.*?)(?=RECOMENDACIONES:|VALIDACIÓN HUMANA:|$)', respuesta, re.DOTALL | re.IGNORECASE)
        if not match:
            return {"predicciones": []}

        lines = [line.strip('-* \t') for line in match.group(1).splitlines() if line.strip()]
        return {"predicciones": lines[:5]}

    def _extraer_factores_riesgo(self, respuesta: str) -> Dict[str, Any]:
        match = re.search(r'OBSERVACIONES:\s*(.*?)(?=ANOMALÍAS Y ERRORES:|PRIORIDAD:|RECOMENDACIONES:|VALIDACIÓN HUMANA:|$)', respuesta, re.DOTALL | re.IGNORECASE)
        if not match:
            return {"factores": []}

        lines = [line.strip('-* \t') for line in match.group(1).splitlines() if line.strip()]
        return {"factores": lines[:5]}

    def _extraer_recomendaciones(self, respuesta: str) -> str:
        match = re.search(r'RECOMENDACIONES:\s*\n(.*?)(?=VALIDACIÓN HUMANA:|$)', respuesta, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else "Consulte con su médico para validación final."

    async def close(self) -> None:
        if self.session and not self.session.closed:
            await self.session.close()
