"""
Cliente asíncrono para comunicación con Ollama y extracción de JSON robusto.
"""

import aiohttp
import json
import asyncio
import logging
from typing import Dict, Any, Optional
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class OllamaClient:
    """Cliente asíncrono para Ollama con reintentos y manejo de errores."""
    
    def __init__(self, model: str = "medgemma", base_url: str = "http://localhost:11434", timeout: int = 300):
        self.model = model
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_json(
        self,
        prompt: str,
        system: str = "Eres un asistente clínico profesional.",
        temperature: float = 0.3
    ) -> Dict[str, Any]:
        """Genera JSON desde Ollama con reintentos automáticos."""
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))

        try:
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "system": system,
                "stream": False,
                "temperature": temperature,
                "format": "json"
            }

            async with self.session.post(url, json=payload) as response:
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
            logger.error(f"Timeout after {self.timeout}s")
            raise
        except aiohttp.ClientError as e:
            logger.error(f"Connection error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise

    async def generate_text(
        self,
        prompt: str,
        system: str = "Eres un asistente clínico profesional.",
        temperature: float = 0.3
    ) -> str:
        """Genera texto desde Ollama."""
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout))

        try:
            url = f"{self.base_url}/api/generate"
            payload = {
                "model": self.model,
                "prompt": prompt,
                "system": system,
                "stream": False,
                "temperature": temperature
            }

            async with self.session.post(url, json=payload) as response:
                if response.status != 200:
                    logger.error(f"Ollama error {response.status}")
                    return "Error al generar respuesta"

                data = await response.json()
                return data.get("response", "").strip()

        except Exception as e:
            logger.error(f"Error in generate_text: {e}")
            return f"Error: {str(e)}"

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
        if not self.session:
            self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5))

        try:
            url = f"{self.base_url}/api/tags"
            async with self.session.get(url) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Status check failed: {e}")
            return False
