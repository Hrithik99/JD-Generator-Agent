from __future__ import annotations

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import pathlib, json, faiss, numpy as np, hashlib, pickle


from typing import List, Sequence
import numpy as np


# ---------------------------------------------------------------------------
# BASIC RAG UTILS — similarity search over FAISS
# ---------------------------------------------------------------------------

# --- Fallback local embed helper -------------------------------------------
# We expect `openai_model.py` to expose an `embed(text: str) -> np.ndarray`.
# If it doesn’t exist yet (IDE shows yellow squiggle), we stub it so the file
# always runs; you can replace this with your real embedding call later.
try:
    from app.core.openai_model import embed  # type: ignore
except (ImportError, AttributeError):

    def embed(text: str) -> np.ndarray:  # noqa: D401, ANN001
        """Fallback: zero‑vector embedding to keep code runnable."""
        return np.zeros(768, dtype="float32")


EMBED_MODEL = SentenceTransformer("BAAI/bge-base-en-v1.5")

def load_corpus(folder="data/corpus"):
    files = sorted(pathlib.Path(folder).glob("*.txt"))
    texts = [f.read_text(encoding="utf-8") for f in files]
    return files, texts

def build_or_load_faiss(texts):
    cache = pathlib.Path(".faiss_cache.pkl")
    if cache.exists():
        return pickle.loads(cache.read_bytes())
    embs = EMBED_MODEL.encode(texts, convert_to_numpy=True, normalize_embeddings=True)
    index = faiss.IndexFlatIP(embs.shape[1])
    index.add(embs)
    cache.write_bytes(pickle.dumps(index))
    return index

def _safe_clip(ids: Sequence[int], texts: List[str]) -> List[str]:
    """Return only texts that have a matching index within bounds."""
    max_idx = len(texts) - 1
    return [texts[i] for i in ids if 0 <= i <= max_idx]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def retrieve(query: str, texts: List[str], index, *, k: int = 3) -> List[str]:
    """Return the top‑`k` most similar documents to *query*.

    * `index` is a pre‑built FAISS index aligned with *texts* order.
    * Will silently return fewer examples if the index/texts have drifted.
    """
    if not texts:
        return []

    q_vec: np.ndarray = embed(query)

    scores, ids = index.search(q_vec.astype("float32").reshape(1, -1), min(k, len(texts)))

    return _safe_clip(ids[0], texts)