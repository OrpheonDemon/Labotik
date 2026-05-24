from typing import Any
from .rag_engine import RAGEngine
from .ollama_client import OllamaClient
from .prompts import SYSTEM_PROMPT, CHAT_PROMPT_TEMPLATE


class ClinicalAssistant:
    def __init__(self, rag_engine: RAGEngine, ollama_client: OllamaClient):
        self.rag_engine = rag_engine
        self.client = ollama_client

    async def ask(self, question: str, patient_context: str | None = None) -> dict[str, Any]:
        context = patient_context or "Sin contexto clínico adicional."
        rag_result = await self.rag_engine.query(question)
        rag_text = self._build_rag_context(rag_result.get('context_matches', []))

        prompt_context = context
        if rag_text:
            prompt_context = f"{context}\n\nContexto recuperado:\n{rag_text}"

        prompt = CHAT_PROMPT_TEMPLATE.format(
            system_prompt=SYSTEM_PROMPT,
            context=prompt_context,
            question=question
        )
        assistant_text = await self.client.generate(prompt)
        return {
            'query': question,
            'rag_context': rag_result,
            'assistant_response': assistant_text
        }

    def _build_rag_context(self, matches: list[dict[str, Any]]) -> str:
        if not matches:
            return ""
        return "\n\n".join([
            f"Documento: {match.get('id')}\n{match.get('text')}"
            for match in matches
        ])
