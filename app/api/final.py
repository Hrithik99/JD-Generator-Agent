from fastapi import APIRouter, HTTPException
from app.state import load_session, save_session, TEXTS, INDEX
from app.core.generate_full_jd import finalize

router = APIRouter(prefix="/final", tags=["final"])

@router.post("/{sid}")
def create_final(sid: str):
    # Load session from Redis
    sess = load_session(sid)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")

    # Generate full job description
    full_jd = finalize(
        draft_jd=sess["draft"],
        ctx=sess["ctx"],
        corpus_texts=TEXTS,
        index=INDEX,
    )

    # Save updated session
    sess["full"] = full_jd
    save_session(sid, sess)

    return {"full": full_jd}
