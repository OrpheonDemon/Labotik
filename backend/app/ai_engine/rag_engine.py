from typing import Any
from .embeddings_service import EmbeddingsService
from .ollama_client import OllamaClient


class RAGEngine:
    def __init__(self, embeddings_service: EmbeddingsService, ollama_client: OllamaClient):
        self.embeddings = embeddings_service
        self.client = ollama_client

    def index_document(self, doc_id: str, text: str, metadata: dict | None = None) -> None:
        self.embeddings.index_document(doc_id, text, metadata)

    async def query(self, question: str) -> dict[str, Any]:
        matches = self.embeddings.search(question, top_k=3)
        if matches:
            combined = "\n\n".join([
                f"Documento: {item['id']}\n{item['text']}" for item in matches
            ])
        else:
            combined = "No hay documentos indexados que aporten contexto adicional."

        prompt = f"Contexto recuperado:\n{combined}\n\nPregunta:\n{question}\n\nResponde con claridad y sugiere validación humana."
        answer = await self.client.generate(prompt)
        return {
            'question': question,
            'context_matches': matches,
            'answer': answer
        }
