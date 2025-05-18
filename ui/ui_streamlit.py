import sys, pathlib, json
import streamlit as st
from pathlib import Path

# ensure project root on path
sys.path.append(str(Path(__file__).parents[1]))

from app.core.local_model import generate as local_generate
from app.core.openai_model import generate as gpt_generate
from app.core.draft_jd import draft
from app.core.generate_full_jd import finalize, revise_final_jd
from app.core.rag_utils import load_corpus, build_or_load_faiss

# -----------------------------------------------------------------------------
# Corpus & FAISS index load once
# -----------------------------------------------------------------------------
CORPUS_DIR = Path("data/corpus")
_, _texts = load_corpus(CORPUS_DIR)
_FAISS_INDEX = build_or_load_faiss(_texts)

st.set_page_config(page_title="JD Suggestor", layout="wide")
st.title("📝 Job‑Description Suggestor Agent")

# ---------------------------- Sidebar Inputs ---------------------------------
with st.sidebar:
    st.header("Hiring‑Manager Inputs")
    job_title = st.text_input("Job Title*", placeholder="Senior Data Engineer")
    skills = st.text_area("Skills (comma‑separated)*", height=80)
    years_exp = st.number_input("Years of Experience*", min_value=0, max_value=40, value=3)
    education = st.text_input("Education", placeholder="BS in CS or related")
    work_auth = st.text_input("Work Authorization", placeholder="Any / US‑Work‑Permit")
    skip_draft = st.checkbox("Skip to Final JD (uses GPT‑4o only)")

    if st.button("Generate" ) and job_title and skills:
        st.session_state["ctx"] = dict(
            job_title=job_title,
            skills=skills,
            years_exp=years_exp,
            education=education,
            work_auth=work_auth,
        )
        st.session_state["phase"] = "draft_skipped" if skip_draft else "draft"
        for key in ("draft_jd", "full_jd", "version"):
            st.session_state.pop(key, None)
        st.rerun()

# ----------------------------- Draft Phase ------------------------------------
if st.session_state.get("phase") == "draft":
    ctx = st.session_state["ctx"]

    # initial draft
    if "draft_jd" not in st.session_state:
        st.session_state["draft_jd"] = draft(ctx)

    st.subheader("Draft Job Description (Editable)")

    # allow inline editing of JD itself
    edited_draft = st.text_area("Draft JD", value=st.session_state["draft_jd"], height=350, key="draft_text")

    st.markdown("**Manager Feedback / Instructions** (optional)")
    feedback_text = st.text_area("Feedback", key="draft_feedback", height=120)

    col1, col2 = st.columns(2)
    if col1.button("Apply Feedback & Update"):
        st.session_state["draft_jd"] = local_generate(
            f"Manager feedback: {feedback_text}\n\nExisting draft JD:\n{edited_draft}",
            system="Revise the draft JD accordingly. Return full JD.",
            max_tokens=400,
        )
        st.rerun()
    if col2.button("Proceed to Final JD →"):
        st.session_state["phase"] = "final"
        st.session_state["draft_jd"] = edited_draft  # preserve latest edits
        st.rerun()

# ----------------------------- Skip‑Draft branch ------------------------------
if st.session_state.get("phase") == "draft_skipped":
    ctx = st.session_state["ctx"]
    auto_draft = (
        f"Role: {ctx['job_title']}\nSkills: {ctx['skills']}\nYears Exp: {ctx['years_exp']}\nEducation: {ctx['education']}"
    )
    st.session_state["draft_jd"] = auto_draft
    st.session_state["phase"] = "final"
    st.rerun()

# ----------------------------- Final Phase ------------------------------------
if st.session_state.get("phase") == "final":
    ctx = st.session_state["ctx"]
    draft_jd = st.session_state["draft_jd"]

    if "full_jd" not in st.session_state:
        st.session_state["full_jd"] = finalize(draft_jd, ctx, _texts, _FAISS_INDEX)
        st.session_state["version"] = 1

    st.subheader(f"Company‑Aligned JD (v{st.session_state['version']}) – Editable")

    edited_full = st.text_area("Final JD", value=st.session_state["full_jd"], height=450, key="full_text")

    st.markdown("**Manager Feedback / Instructions**")
    feedback_final = st.text_area("Feedback", key="final_feedback", height=120)

    col1, col2 = st.columns(2)
    if col1.button("Revise Final JD"):
        st.session_state["full_jd"] = revise_final_jd(edited_full, feedback_final, ctx)
        st.session_state["version"] += 1
        st.rerun()

    if col2.button("Approve & Save"):
        save_path = Path("data/saves/final_jd_latest.txt")
        save_path.write_text(edited_full, encoding="utf-8")
        st.success(f"Saved to {save_path.resolve()}")
