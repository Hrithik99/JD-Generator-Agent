from fastapi import APIRouter, HTTPException, Body
from app.core.generate_full_jd import revise_final_jd
from app.state import load_session, save_session, delete_session

router = APIRouter(prefix="/revise", tags=["revise"])

@router.post("/{sid}")
def revise(sid: str, feedback: str = Body(...)):
    sess = load_session(sid)
    if not sess or "full" not in sess:
        raise HTTPException(404, "no final JD yet")
    new = revise_final_jd(sess["full"], feedback, sess["ctx"])
    sess["full"] = new
    save_session(sid, sess)
    return {"full": new}

# optional delete endpoint
@router.delete("/{sid}")
def delete(sid: str):
    delete_session(sid)
    return {"detail": "session deleted"}