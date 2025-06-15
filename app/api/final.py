from __future__ import annotations

import os
from fastapi import APIRouter, HTTPException, Body

from app.state import load_session, save_session, TEXTS, INDEX
from app.core.generate_full_jd import finalize

router = APIRouter(prefix="/final", tags=["final"])


@router.post("/{sid}")
def create_final(
    sid: str,
    company_url: str | None = Body(default=None, embed=True),  # optional; UI might omit
):
    """Generate the *company‑aligned* job description for the given session.

    Resolution order for the company link:
      1. `company_url` passed in the request body.
      2. `sess['ctx']['company_url']` if already stored.
      3. `COMPANY_URL` environment variable.
    If no link is found, finalize() still works – it simply omits the
    "About the Company" section.
    """

    # ------------------------------------------------------------------ #
    # 1. Load session (stored in Redis)
    # ------------------------------------------------------------------ #
    sess = load_session(sid)
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")

    # ------------------------------------------------------------------ #
    # 2. Inject / resolve the company URL
    # ------------------------------------------------------------------ #
    if company_url:
        # Highest precedence – explicit body field
        sess["ctx"]["company_url"] = company_url
    else:
        # Use existing value or fallback to env var
        sess["ctx"].setdefault("company_url", os.getenv("COMPANY_URL"))

    # Extract the resolved URL so we can pass it explicitly
    resolved_url: str | None = sess["ctx"].get("company_url")

    # ------------------------------------------------------------------ #
    # 3. Generate full JD
    # ------------------------------------------------------------------ #
    full_jd = finalize(
        draft_jd=sess["draft"],
        ctx=sess["ctx"],
        corpus_texts=TEXTS,
        index=INDEX,
        company_url=resolved_url,  # ← satisfy the required kw‑only arg
    )

    # ------------------------------------------------------------------ #
    # 4. Persist & return
    # ------------------------------------------------------------------ #
    sess["full"] = full_jd
    save_session(sid, sess)

    return {"full": full_jd}
