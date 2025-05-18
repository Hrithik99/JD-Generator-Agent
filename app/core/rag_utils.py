from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import pathlib, json, faiss, numpy as np, hashlib, pickle

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

def retrieve(query, texts, index, k=3):
    q_emb = EMBED_MODEL.encode([query], normalize_embeddings=True)
    sims, ids = index.search(np.array(q_emb, dtype="float32"), k)
    return [texts[i] for i in ids[0]]
