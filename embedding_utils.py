import hashlib
import os
from typing import List


def _deterministic_embedding(text: str, dim: int = 384) -> List[float]:
    normalized = (text or "").strip().lower()
    if not normalized:
        return [0.0] * dim

    values: List[float] = []
    for i in range(dim):
        token = f"{normalized}:{i}".encode("utf-8")
        digest = hashlib.blake2b(token, digest_size=8).digest()
        value = ((digest[0] << 8) | digest[1]) / 65535.0
        values.append((value * 2.0) - 1.0)
    return values


def embed_text(text: str) -> List[float]:
    try:
        from sentence_transformers import SentenceTransformer
    except Exception:
        return _deterministic_embedding(text, dim=384)

    model_name = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    try:
        import functools

        @functools.lru_cache(maxsize=1)
        def _load_model():
            return SentenceTransformer(model_name)

        embedding = _load_model().encode(text, normalize_embeddings=True)
        return [float(value) for value in embedding[:384]]
    except Exception:
        return _deterministic_embedding(text, dim=384)


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    norm_a = sum(a * a for a in vec1) ** 0.5
    norm_b = sum(b * b for b in vec2) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)
