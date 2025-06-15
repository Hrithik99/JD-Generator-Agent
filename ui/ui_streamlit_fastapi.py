"""
ui/ui_streamlit.py  –  thin Streamlit client that talks to FastAPI
------------------------------------------------------------------
Environment:
  API_URL   (optional)  e.g. http://localhost:8000   – defaults to same
"""

import os, requests, streamlit as st
from dotenv import load_dotenv
load_dotenv()

API = "http://backend:8000"
company_URL=os.getenv('COMPANY_URL')
company_name=os.getenv('COMPANY_NAME')
job_type=os.getenv('JOB_TYPE')
job_location=os.getenv('JOB_LOCATION')
print(API)
st.set_page_config(page_title="JD Generator", layout="wide")
st.title("📝 Job‑Description Suggestor (API‑driven)")

# ------------------------------------------------ Sidebar form ----------------------------------------------------
with st.sidebar:
    st.header("Hiring‑Manager Inputs")
    job_title = st.text_input("Job Title *", placeholder="Senior Data Engineer")
    context    = st.text_area("Enter your desired candidates qualities*", height=150)
    years_exp = st.number_input("Years of Experience", 0, 40, 3)
    skip_draft = st.checkbox("Skip to Final JD (GPT‑4o only)")

    if st.button("Generate JD") and job_title:
        ctx = {
            "job_title": job_title,
            "context": context,
            "years_exp": years_exp,
            "company_name" : company_name,
            "job_type":job_type,
            "job_location":job_location
        }
        try:
            resp = requests.post(f"{API}/draft", json=ctx, timeout=120).json()
            st.session_state.sid   = resp["session_id"]
            st.session_state.draft = resp["draft"]
            st.session_state.phase = "final" if skip_draft else "draft"
            st.rerun()
        except Exception as e:
            st.error(f"API error: {e}")

    if st.button("🔄  New Session"):
        st.session_state.clear()
        st.rerun()   # or st.rerun() if on new Streamlit

# ------------------------------------------------ Draft phase -----------------------------------------------------
# ------------------------------------------------ Draft phase -----------------------------------------------------
if st.session_state.get("phase") == "draft":
    st.subheader("Draft Job Description")

    # ── COLLAPSIBLE source editor ────────────────────────────────────────────
    with st.expander("✏️  Edit Markdown source (optional)", expanded=False):
        draft_area = st.text_area(
            label="",
            value=st.session_state.draft,
            height=350,
            key="draft_edit",
        )
        # keep the edits in session for later phases
        st.session_state.draft = draft_area

    # ── SCROLLABLE live preview ─────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="max-height:500px; overflow:auto; border:1px solid #eaeaea; padding:1rem;">
            {st.session_state.draft}
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("Proceed to Final JD →"):
        st.session_state.phase = "final"
        st.rerun()

# ------------------------------------------------ Final phase -----------------------------------------------------
if st.session_state.get("phase") == "final":
    # First fetch full JD if not already cached
    if "full" not in st.session_state:
        try:
            payload={}
            if company_URL:
                payload["company_url"] = company_URL            
            st.session_state.full = requests.post(
                f"{API}/final/{st.session_state.sid}",
                json=payload,          # ← ← NOW we include the JSON body
                timeout=120,
            ).json()["full"]
        except Exception as e:
            st.error(f"API error: {e}")
            st.stop()

    st.subheader("Company‑Aligned JD")
    # ── COLLAPSIBLE source editor ────────────────────────────────────────────
    with st.expander("✏️  Edit Markdown source (optional)", expanded=False):
        jd_area = st.text_area(
            label="",
            value=st.session_state.full,
            height=450,
            key="jd_edit",
        )
        # write-back so preview + backend stay in sync
        st.session_state.full = jd_area

    # ── SCROLLABLE live preview ─────────────────────────────────────────────
    st.markdown(
        f"""
        <div style="max-height:600px; overflow:auto; border:1px solid #eaeaea; padding:1rem;">
            {jd_area}
        </div>
        """,
        unsafe_allow_html=True,
    )



    feedback = st.text_area("Manager Feedback (optional)", height=120)

    col1, col2 = st.columns(2)
    if col1.button("Revise with Feedback"):
        try:
            resp = requests.post(
                f"{API}/revise/{st.session_state.sid}",
                json=feedback,              # ← send as JSON, not form‑data
                timeout=120,
            ).json()
            st.session_state.full = resp["full"]
            st.rerun()
        except Exception as e:
            st.error(f"API error: {e}")

    if col2.button("Approve & Download"):
        try:
            # 1️⃣  Tell FastAPI to persist the JD
            resp = requests.post(
                f"{API}/approve/{st.session_state.sid}",
                timeout=30,
            ).json()                                  # → {"job_id": "..."}
            job_id = resp["job_id"]

            # 2️⃣  Offer the download right away
            st.download_button(
                label="Download JD as txt",
                data=jd_area,
                file_name=f"{job_id}.txt",
                mime="text/plain",
            )
            st.success(f"✅ Saved as {job_id}.json in data/saves/")
        except Exception as e:
            st.error(f"API error: {e}")
