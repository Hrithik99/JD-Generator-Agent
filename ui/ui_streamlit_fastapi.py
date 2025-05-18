"""
ui/ui_streamlit.py  –  thin Streamlit client that talks to FastAPI
------------------------------------------------------------------
Environment:
  API_URL   (optional)  e.g. http://localhost:8000   – defaults to same
"""

import os, requests, streamlit as st

API = "http://127.0.0.1:8000"
print(API)
st.set_page_config(page_title="JD Generator", layout="wide")
st.title("📝 Job‑Description Suggestor (API‑driven)")

# ------------------------------------------------ Sidebar form ----------------------------------------------------
with st.sidebar:
    st.header("Hiring‑Manager Inputs")
    job_title = st.text_input("Job Title *", placeholder="Senior Data Engineer")
    skills    = st.text_area("Skills (comma separated) *", height=80)
    years_exp = st.number_input("Years of Experience", 0, 40, 3)
    education = st.text_input("Education", placeholder="BS in CS or related")
    work_auth = st.text_input("Work Authorization", placeholder="Any / US‑Permit")
    skip_draft = st.checkbox("Skip to Final JD (GPT‑4o only)")

    if st.button("Generate JD") and job_title and skills:
        ctx = {
            "job_title": job_title,
            "skills": skills,
            "years_exp": years_exp,
            "education": education,
            "work_auth": work_auth,
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
if st.session_state.get("phase") == "draft":
    st.subheader("Draft Job Description")
    st.code(st.session_state.draft, language="markdown")

    if st.button("Proceed to Final JD →"):
        st.session_state.phase = "final"
        st.rerun()

# ------------------------------------------------ Final phase -----------------------------------------------------
if st.session_state.get("phase") == "final":
    # First fetch full JD if not already cached
    if "full" not in st.session_state:
        try:
            st.session_state.full = requests.post(
                f"{API}/final/{st.session_state.sid}", timeout=120
            ).json()["full"]
        except Exception as e:
            st.error(f"API error: {e}")
            st.stop()

    st.subheader("Company‑Aligned JD")
    jd_area = st.text_area("Editable JD", value=st.session_state.full, height=450)

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
        st.download_button(
            label="Download JD as txt",
            data=jd_area,
            file_name="job_description.txt",
            mime="text/plain",
        )
        st.success("JD approved and ready to post!")
