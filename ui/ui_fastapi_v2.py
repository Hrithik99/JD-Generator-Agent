import os, requests, streamlit as st

API = os.getenv("API_URL", "http://127.0.0.1:8000")
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
            "years_exp": years_exp
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
        st.rerun()

# ------------------------------------------------ Draft phase -----------------------------------------------------
if st.session_state.get("phase") == "draft":
    st.subheader("Draft Job Description (Editable)")
    draft_area = st.text_area("Draft JD", value=st.session_state.draft, height=350)

    feedback_draft = st.text_area("Manager Feedback / Instructions (optional)", height=120)

    col1, col2 = st.columns(2)
    if col1.button("Apply Feedback & Update"):
        try:
            prompt = {
                "job_title": st.session_state.get("job_title"),
                "context": feedback_draft,
                "years_exp": years_exp,
                "draft": draft_area
            }
            # You may replace this with an actual update endpoint if needed
            st.session_state.draft = draft_area + "\n\n# Revised based on feedback: " + feedback_draft
            st.rerun()
        except Exception as e:
            st.error(f"Error updating draft: {e}")

    if col2.button("Proceed to Final JD →"):
        st.session_state.phase = "final"
        st.session_state.draft = draft_area
        st.rerun()

# ------------------------------------------------ Final phase -----------------------------------------------------
if st.session_state.get("phase") == "final":
    if "full" not in st.session_state:
        try:
            st.session_state.full = requests.post(
                f"{API}/final/{st.session_state.sid}", timeout=120
            ).json()["full"]
        except Exception as e:
            st.error(f"API error: {e}")
            st.stop()

    st.subheader("Company‑Aligned JD (Editable)")
    jd_area = st.text_area("Final JD", value=st.session_state.full, height=450)

    feedback = st.text_area("Manager Feedback / Instructions", height=120)

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
        st.download_button(
            label="Download JD as txt",
            data=jd_area,
            file_name="job_description.txt",
            mime="text/plain",
        )
        st.success("JD approved and ready to post!")
