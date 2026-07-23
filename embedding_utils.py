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
