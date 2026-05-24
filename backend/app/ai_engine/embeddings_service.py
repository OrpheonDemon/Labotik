import hashlib
import math
from typing import Any


class EmbeddingsService:
    def __init__(self):
        self.index: list[dict[str, Any]] = []

    def create_embedding(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode('utf-8')).digest()
        return [b / 255 for b in digest]

    def index_document(self, doc_id: str, text: str, metadata: dict | None = None) -> None:
        self.index = [item for item in self.index if item['id'] != doc_id]
        vector = self.create_embedding(text)
        self.index.append({
            'id': doc_id,
            'vector': vector,
            'metadata': metadata or {},
            'text': text
        })

    def similarity(self, a: list[float], b: list[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def search(self, query: str, top_k: int = 3) -> list[dict[str, Any]]:
        query_vector = self.create_embedding(query)
        scored = [
            {**item, 'score': self.similarity(query_vector, item['vector'])}
            for item in self.index
        ]
        scored.sort(key=lambda item: item['score'], reverse=True)
        return scored[:top_k]
