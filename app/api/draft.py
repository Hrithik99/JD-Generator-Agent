from fastapi import APIRouter, Body, HTTPException
from uuid import uuid4
from app.core.draft_jd import draft
from app.state import save_session
from app.core.draft_jd import revise_draft_jd, summarize_revision_change  # you'll create this module
from app.state import load_session




router = APIRouter(prefix="/draft", tags=["draft"])

@router.post("/")
def create(payload: dict = Body(...)):
    out = draft(payload)
    sid = str(uuid4())

    save_session(sid, {
        "ctx": payload,
        "draft": out["draft"],
        "follow_up": out["follow_up"],
        "history": [],
        "revision_summary": ""
    })
    resp={
        "session_id": sid,
        "draft": out["draft"],
        "follow_up": out["follow_up"]
    }
    return resp


@router.post("/revise_draft/{sid}")
def revise_draft(sid: str, input: dict = Body(...)):
    sess = load_session(sid)
    if not sess or "draft" not in sess:
        raise HTTPException(404, "No draft JD found for this session")

    # Get past summary
    revision_summary = sess.get("revision_summary", "")

    # Run revision
    output = revise_draft_jd(sess["draft"], input["input"], sess["ctx"], revision_summary)

    # Update session
    sess["draft"] = output["draft"]
    sess["follow_up"] = output["follow_up"]
    sess.setdefault("history", []).append({
        "input": input["input"],
        "output": output["draft"],
        "follow_up": output["follow_up"]
    })

    # Smart summary line using LLM
    job_title = sess["ctx"].get("job_title", "Unknown Role")
    summary_line = summarize_revision_change(
        old_draft=sess["draft"],
        new_draft=output["draft"],
        user_input=input["input"],
        job_title=job_title
    )

    revision_lines = sess.get("revision_summary", "").splitlines()
    sess["revision_summary"] = "\n".join(revision_lines + [f"- {summary_line}"])


    save_session(sid, sess)
    return output
