import os
import json
from redis import Redis
from app.core.rag_utils import load_corpus, build_or_load_faiss

# Load and index corpus once
FILES, TEXTS = load_corpus("data/corpus")
INDEX = build_or_load_faiss(TEXTS)

# Redis configuration — defaults to localhost for local dev
REDIS_HOST = os.getenv("REDIS_HOST", "127.0.0.1")  # fallback to localhost if not set
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

# Redis connection object
rdb = Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

# Redis key helpers
def _key(sid: str) -> str:
    return f"jd_session:{sid}"

def save_session(sid: str, obj: dict):
    rdb.setex(_key(sid), 14 * 24 * 3600, json.dumps(obj))  # 14-day TTL

def load_session(sid: str) -> dict | None:
    raw = rdb.get(_key(sid))
    return json.loads(raw) if raw else None

def delete_session(sid: str):
    rdb.delete(_key(sid))
