import aiohttp
import asyncio
import logging
from typing import Any

logger = logging.getLogger(__name__)


class OllamaClient:
    def __init__(self, model: str = "medgemma", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url.rstrip('/')
        self.api_url = f"{self.base_url}/api"
        self.session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session

    async def verify_connection(self) -> bool:
        try:
            session = await self._get_session()
            async with session.get(f"{self.api_url}/models", timeout=aiohttp.ClientTimeout(total=5)) as resp:
                return resp.status == 200
        except Exception as exc:
            logger.error(f"Error verificando conexión con Ollama: {exc}")
            return False

    async def generate(self, prompt: str, temperature: float = 0.2, max_tokens: int = 800) -> str:
        session = await self._get_session()
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        try:
            async with session.post(f"{self.api_url}/generate", json=payload, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                text = await resp.text()
                if resp.status != 200:
                    logger.error(f"Ollama API error {resp.status}: {text}")
                    raise Exception(f"Ollama API error: {resp.status}")
                data = await resp.json()
                return data.get("response", data.get("text", "")).strip()
        except asyncio.TimeoutError:
            raise Exception("Timeout esperando respuesta de Ollama")
        except Exception as exc:
            logger.error(f"Error generando texto en Ollama: {exc}")
            raise

    async def close(self) -> None:
        if self.session and not self.session.closed:
            await self.session.close()
