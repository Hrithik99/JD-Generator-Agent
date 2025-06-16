"""
ui/ui_streamlit.py  –  thin Streamlit client that talks to FastAPI
------------------------------------------------------------------
Environment:
  API_URL   (optional)  e.g. http://localhost:8000   – defaults to same
"""

import os, requests, streamlit as st
import warnings

warnings.filterwarnings("ignore")
from dotenv import load_dotenv

load_dotenv()

# API & env defaults -------------------------------------------------
#API = os.getenv("API_URL")
API = "http://127.0.0.1:8000"
company_URL = os.getenv("COMPANY_URL")
company_name = os.getenv("COMPANY_NAME")
job_type = os.getenv("JOB_TYPE")
job_location = os.getenv("JOB_LOCATION")

# Streamlit page config ----------------------------------------------
st.set_page_config(page_title="JD Generator", layout="wide")
st.title("📝 Job-Description Suggestor")

# --- session defaults (NEW) -----------------------------------------
for k, v in {"follow_up": "", "history": []}.items():
    st.session_state.setdefault(k, v)
# --------------------------------------------------------------------

# ------------------------------------------------ Sidebar form -------------------------------------------
with st.sidebar:
    st.header("Hiring-Manager Inputs")
    job_title = st.text_input("Job Title *", placeholder="Senior Data Engineer")
    context = st.text_area("Enter your desired candidates qualities*", height=150)
    years_exp = st.number_input("Years of Experience", 0, 40, 3)
    skip_draft = st.checkbox("Skip to Final JD (GPT-4o only)")

    # --- Generate JD -------------------------------------------------
    if st.button("Generate JD") and job_title:
        ctx = {
            "job_title": job_title,
            "context": context,
            "years_exp": years_exp,
            "company_name": company_name,
            "job_type": job_type,
            "job_location": job_location,
        }
        try:
            resp = requests.post(f"{API}/draft", json=ctx, timeout=120).json()
            st.session_state.sid = resp["session_id"]
            st.session_state.draft = resp.get("draft","")
            st.session_state.follow_up = resp.get("follow_up", "")  # NEW
            st.session_state.phase = "final" if skip_draft else "draft"
            st.rerun()
        except Exception as e:
            st.error(f"API error: {e}")

    # --- New Session -------------------------------------------------
    if st.button("🔄  New Session"):
        st.session_state.clear()
        st.session_state.follow_up = ""   # NEW
        st.session_state.history = []     # NEW
        st.rerun()

# ------------------------------------------------ Draft phase --------------------------------------------
if st.session_state.get("phase") == "draft":
    st.subheader("📝 Draft Job Description")

    # Editable JD block
    st.text_area(
        label="✏️ Edit Draft JD (Text Format)",
        value=st.session_state.draft,
        height=400,
        key="draft_edit",
    )
    st.session_state.draft = st.session_state.draft_edit


    # Show LLM-generated follow-up if available

    if st.session_state.get("follow_up"):
        st.markdown("### 🤖 Follow-Up Suggestion")
        st.info(st.session_state.follow_up)

        if st.button("✅ Accept and Revise with Follow-Up"):
            try:
                resp = requests.post(
                    f"{API}/draft/revise_draft/{st.session_state.sid}",
                    json={"input": st.session_state.follow_up},
                    timeout=120,
                ).json()
                st.session_state.draft = resp["draft"]
                st.session_state.follow_up = resp["follow_up"]
                st.rerun()
            except Exception as e:
                st.error(f"API error: {e}")

    # Add feedback to revise draft
    st.text_area(
        label="➕ Add More Details (e.g., skills, requirements, preferences)",
        placeholder="E.g. Apache Spark, leadership experience, cloud exposure...",
        key="draft_feedback",
        height=80,
    )



    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔁 Revise Draft with Input"):
            try:
                resp = requests.post(
                    f"{API}/draft/revise_draft/{st.session_state.sid}",
                    json={"input": st.session_state.draft_feedback},
                    timeout=120,
                ).json()
                st.session_state.draft = resp["draft"]
                st.session_state.follow_up = resp["follow_up"]
                st.rerun()
            except Exception as e:
                st.error(f"API error: {e}")

    with col2:
        if st.button("➡️ Proceed to Final JD"):
            st.session_state.phase = "final"
            st.rerun()

    # Revision history viewer
    if st.session_state.get("history"):
        with st.expander("🕓 Revision History", expanded=False):
            for i, h in enumerate(st.session_state["history"]):
                st.markdown(f"**🗒️ Input {i+1}:** {h['input']}")
                st.markdown(f"**📌 Follow-Up {i+1}:** {h['follow_up']}")
                st.markdown("---")

# ------------------------------------------------ Final phase --------------------------------------------
if st.session_state.get("phase") == "final":
    # Fetch full JD if not yet cached
    if "full" not in st.session_state:
        try:
            payload = {}
            if company_URL:
                payload["company_url"] = company_URL
            st.session_state.full = requests.post(
                f"{API}/final/{st.session_state.sid}",
                json=payload,
                timeout=120,
            ).json()["full"]
        except Exception as e:
            st.error(f"API error: {e}")
            st.stop()

    st.subheader("🏢 Company-Aligned JD")
    # Collapsible editor
    with st.expander("✏️  Edit Markdown source (optional)", expanded=False):
        jd_area = st.text_area(
            label="",
            value=st.session_state.full,
            height=450,
            key="jd_edit",
        )
        st.session_state.full = jd_area

    # Live preview
    # ── SCROLLABLE live preview ─────────────────────────────────────────────
    st.markdown(
        """
        <style>
        .scroll-box {max-height:600px; overflow:auto;
                    border:1px solid #eaeaea; padding:1rem;}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown(f'<div class="scroll-box">\n\n{st.session_state.full}\n\n</div>',
                unsafe_allow_html=True)


    # Manager feedback
    feedback = st.text_area("🔁 Manager Feedback", height=80)

    col1, col2 = st.columns(2)
    if col1.button("Revise with Feedback"):
        try:
            resp = requests.post(
                f"{API}/revise/{st.session_state.sid}",
                json=feedback,
                timeout=120,
            ).json()
            st.session_state.full = resp["full"]
            st.rerun()
        except Exception as e:
            st.error(f"API error: {e}")

    if col2.button("Approve & Download"):
        try:
            # Tell FastAPI to persist the JD
            resp = requests.post(
                f"{API}/approve/{st.session_state.sid}",
                timeout=30,
            ).json()
            job_id = resp["job_id"]

            # Offer download
            st.download_button(
                label="Download JD as txt",
                data=jd_area,
                file_name=f"{job_id}.txt",
                mime="text/plain",
            )
            st.success(f"✅ Saved as {job_id}.json in data/saves/")
        except Exception as e:
            st.error(f"API error: {e}")
