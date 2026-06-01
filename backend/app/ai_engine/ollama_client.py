"""
Cliente asíncrono para comunicación con Ollama y extracción de JSON robusto.
"""

import aiohttp
import json
import asyncio
import logging
from typing import Dict, Any, Optional, AsyncGenerator
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class OllamaClient:
    """Cliente asíncrono para Ollama con reintentos, verificación de modelos y manejo de errores."""
    
    def __init__(self, model: str = "medgemma", base_url: str = "http://localhost:11434", timeout: int = 300):
        self.model = model
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self._verified_model: Optional[str] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def close(self):
        """Cierra la sesión aiohttp de manera segura."""
        if self.session and not self.session.closed:
            await self.session.close()

    def _get_session(self) -> aiohttp.ClientSession:
        """Obtiene o inicializa la sesión aiohttp de manera segura."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def _ensure_model(self) -> str:
        """Verifica que el modelo configurado esté instalado, de lo contrario advierte de su ausencia."""
        if self._verified_model:
            return self._verified_model

        session = self._get_session()
        try:
            url = f"{self.base_url}/api/tags"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    models = [m.get("name") for m in data.get("models", [])]
                    
                    installed_models = []
                    for m in models:
                        installed_models.append(m)
                        if ":" in m:
                            installed_models.append(m.split(":")[0])
                    
                    if self.model in installed_models or f"{self.model}:latest" in installed_models:
                        self._verified_model = self.model
                        return self._verified_model
                    else:
                        logger.error(f"¡ATENCIÓN! El modelo clínico requerido '{self.model}' no está instalado en Ollama.")
                        logger.error("Por favor, ejecuta en la terminal: ollama pull medgemma")
        except Exception as e:
            logger.error(f"Error al verificar modelo en Ollama: {e}")
        
        # Retornar el modelo configurado por defecto (medgemma) de forma estricta
        self._verified_model = self.model
        return self._verified_model

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_json(
        self,
        prompt: str,
        system: str = "Eres un asistente clínico profesional.",
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """Genera JSON desde Ollama con reintentos automáticos."""
        session = self._get_session()
        try:
            url = f"{self.base_url}/api/generate"
            model_to_use = await self._ensure_model()
            payload = {
                "model": model_to_use,
                "prompt": prompt,
                "system": system,
                "stream": False,
                "temperature": temperature,
                "format": "json",
                "keep_alive": "30m",
                "options": {
                    "num_predict": 512,
                    "num_ctx": 4096,
                }
            }

            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                if response.status != 200:
                    logger.error(f"Ollama error {response.status}: {await response.text()}")
                    raise Exception(f"Ollama HTTP {response.status}")

                data = await response.json()
                response_text = data.get("response", "")

                # Extrae JSON robustamente
                try:
                    json_match = self._extract_json(response_text)
                    if json_match:
                        return json.loads(json_match)
                    else:
                        return {"error": "No JSON found", "raw": response_text}
                except json.JSONDecodeError as e:
                    logger.error(f"JSON decode error: {e}")
                    return {"error": "Invalid JSON", "raw": response_text[:500]}

        except asyncio.TimeoutError:
            logger.error(f"Timeout after {self.timeout}s during JSON generation")
            raise
        except aiohttp.ClientError as e:
            logger.error(f"Connection error during JSON generation: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error during JSON generation: {e}")
            raise

    async def generate_text(
        self,
        prompt: str,
        system: str = "Eres un asistente clínico profesional.",
        temperature: float = 0.3
    ) -> str:
        """Genera texto desde Ollama."""
        session = self._get_session()
        try:
            url = f"{self.base_url}/api/generate"
            model_to_use = await self._ensure_model()
            payload = {
                "model": model_to_use,
                "prompt": prompt,
                "system": system,
                "stream": False,
                "temperature": temperature,
                "keep_alive": "30m",
                "options": {
                    "num_predict": 512,
                    "num_ctx": 4096,
                }
            }

            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                if response.status != 200:
                    logger.error(f"Ollama error {response.status}")
                    return "Error al generar respuesta"

                data = await response.json()
                return data.get("response", "").strip()

        except Exception as e:
            logger.error(f"Error in generate_text: {e}")
            return f"Error: {str(e)}"

    async def generate_text_stream(
        self,
        prompt: str,
        system: str = "Eres un asistente clínico profesional.",
        temperature: float = 0.3
    ) -> AsyncGenerator[str, None]:
        """Genera texto desde Ollama con streaming token-por-token."""
        session = self._get_session()
        try:
            url = f"{self.base_url}/api/generate"
            model_to_use = await self._ensure_model()
            payload = {
                "model": model_to_use,
                "prompt": prompt,
                "system": system,
                "stream": True,
                "temperature": temperature,
                "keep_alive": "30m",
                "options": {
                    "num_predict": 512,
                    "num_ctx": 4096,
                }
            }

            async with session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=self.timeout)) as response:
                if response.status != 200:
                    logger.error(f"Ollama stream error {response.status}")
                    yield "Error al generar respuesta"
                    return

                async for line in response.content:
                    if line:
                        try:
                            chunk = json.loads(line.decode('utf-8'))
                            token = chunk.get("response", "")
                            if token:
                                yield token
                            if chunk.get("done", False):
                                return
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            logger.error(f"Error in generate_text_stream: {e}")
            yield f"Error: {str(e)}"

    @staticmethod
    def _extract_json(text: str) -> Optional[str]:
        """Extrae el primer JSON válido de un texto."""
        start = text.find('{')
        if start == -1:
            return None

        depth = 0
        for i in range(start, len(text)):
            if text[i] == '{':
                depth += 1
            elif text[i] == '}':
                depth -= 1
                if depth == 0:
                    return text[start:i+1]

        return None

    async def check_status(self) -> bool:
        """Verifica si Ollama está disponible."""
        session = self._get_session()
        try:
            url = f"{self.base_url}/api/tags"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Status check failed: {e}")
            return False
