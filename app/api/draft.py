from fastapi import APIRouter, Body
from uuid import uuid4
from app.core.draft_jd import draft
from app.state import save_session

router = APIRouter(prefix="/draft", tags=["draft"])

@router.post("/")
def create(payload: dict = Body(...)):
    jd = draft(payload)
    sid = str(uuid4())
    save_session(sid, {"ctx": payload, "draft": jd})
    return {"session_id": sid, "draft": jd}
