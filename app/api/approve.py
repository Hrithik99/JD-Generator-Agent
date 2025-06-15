from __future__ import annotations

import json, os, datetime as dt
from pathlib import Path

from fastapi import APIRouter, HTTPException
from app.state import load_session
import re



router = APIRouter(prefix="/approve", tags=["approve"])

SAVE_DIR = Path("data/saves")
SAVE_DIR.mkdir(parents=True, exist_ok=True)

def safe_filename(text: str) -> str:
    """Sanitize filename by removing unsafe characters."""
    text = text.strip().replace(" ", "_")
    return re.sub(r"[^a-zA-Z0-9_\-]", "", text)


@router.post("/{sid}")
def approve_jd(sid: str):
    """Persist the final JD + ctx into data/saves/ as <job_title>_<UTC>.json"""
    sess = load_session(sid)
    if not sess or "full" not in sess:
        raise HTTPException(404, "Session not ready for approval")

    title_raw = sess["ctx"].get("job_title", "Untitled")
    title = safe_filename(title_raw)
    ts = dt.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    job_id = f"{title}_{ts}"

    payload = {
        "job_id": job_id,
        "timestamp": ts,
        "ctx": sess["ctx"],
        "job_description": sess["full"],
    }

    with open(SAVE_DIR / f"{job_id}.json", "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return {"job_id": job_id}
