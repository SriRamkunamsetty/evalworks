import math
import re
from collections import Counter

from indirectinject.models import DocumentChunk, PoisonStrategy


class MemoryVectorStore:
    """In-memory vector store with chunking and TF-IDF cosine similarity retrieval."""

    def __init__(self):
        self.chunks: list[DocumentChunk] = []

    def clear(self) -> None:
        self.chunks.clear()

    def add_document(
        self,
        doc_name: str,
        content: str,
        poison_strategy: PoisonStrategy | None = None,
        poison_chunk_indices: list[int] | None = None,
    ) -> list[DocumentChunk]:
        """Split document into chunks and store in index."""
        raw_chunks = [p.strip() for p in re.split(r"\n\s*\n+", content) if p.strip()]
        if not raw_chunks:
            raw_chunks = [content.strip()]

        created_chunks = []
        for i, text in enumerate(raw_chunks):
            is_p = (
                poison_strategy is not None
                and poison_chunk_indices is not None
                and i in poison_chunk_indices
            )
            chunk = DocumentChunk(
                doc_name=doc_name,
                text=text,
                is_poisoned=is_p,
                poison_strategy=poison_strategy if is_p else None,
            )
            self.chunks.append(chunk)
            created_chunks.append(chunk)

        return created_chunks

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", text.lower())

    @classmethod
    def _cosine_similarity(cls, query_tokens: list[str], doc_tokens: list[str]) -> float:
        if not query_tokens or not doc_tokens:
            return 0.0

        q_vec = Counter(query_tokens)
        d_vec = Counter(doc_tokens)

        dot = sum(q_vec[t] * d_vec[t] for t in q_vec if t in d_vec)
        q_norm = math.sqrt(sum(v * v for v in q_vec.values()))
        d_norm = math.sqrt(sum(v * v for v in d_vec.values()))

        if q_norm == 0 or d_norm == 0:
            return 0.0
        return dot / (q_norm * d_norm)

    def retrieve(self, query: str, top_k: int = 3) -> list[DocumentChunk]:
        """Retrieve top-K most similar document chunks for a query."""
        if not self.chunks:
            return []

        q_tokens = self._tokenize(query)
        scored_chunks: list[tuple[float, DocumentChunk]] = []

        for chunk in self.chunks:
            d_tokens = self._tokenize(chunk.text)
            sim = self._cosine_similarity(q_tokens, d_tokens)

            # Boost chunk slightly if query keywords are explicitly embedded in chunk
            for t in q_tokens:
                if t in d_tokens:
                    sim = min(1.0, sim + 0.15)

            chunk_copy = chunk.model_copy()
            chunk_copy.similarity_score = round(sim, 4)
            scored_chunks.append((sim, chunk_copy))

        # Sort descending by similarity
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [c for _, c in scored_chunks[:top_k]]
