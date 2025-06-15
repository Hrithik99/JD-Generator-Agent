# generate_full_jd.py
from __future__ import annotations
from .rag_utils import retrieve
from .openai_model import generate as gpt_generate
import json, textwrap,os
from .md_cleaning import clean_markdown

def generate_about_company(
    company_url: str,
    *,
    words_min: int = 100,
    words_max: int = 150,
    model_max_tokens: int = 550,
) -> str:
    """Generate a polished “About the Company” section (≈300‑400 words).

    The section is produced by GPT‑4o using the public company URL for research
    and is meant to appear at the very top of the final job description.
    """
    system = (
        "You are an experienced employer‑branding copywriter. "
        "Craft a compelling, inclusive and engaging 'About the Company' section "
        f"between {words_min} and {words_max} words."
    )
    prompt = textwrap.dedent(
        f"""
        ### Company Website
        {company_url}

        ### Task
        Write the 'About the Company' section (do **not** exceed {words_max} words).
        Make sure you return the output of the task in Markdown Format.
        """
    )

    out=gpt_generate(prompt, system, max_tokens=model_max_tokens).strip()
    about= clean_markdown(out)

    return about


def finalize(
    draft_jd: str,
    ctx: dict,
    corpus_texts: List[str],
    index,
    *,
    k: int = 3,
    company_url: Optional[str] = None,
) -> str:
    """Return a single Markdown JD, optionally preceded by About‑Company."""

    # 1⃣  About‑Company (may be empty)
    company_url = company_url or ctx.get("company_url") or os.getenv("COMPANY_URL")
    about_company = ""
    if company_url:
        try:
            about_company = generate_about_company(company_url)
        except Exception as exc:  # pragma: no cover
            print(f"[warn] About‑company generation failed: {exc}")

    # 2⃣  Retrieve prior JDs for tone mimicry
    examples = retrieve(draft_jd, corpus_texts, index, k=k)

    # 3⃣  Build prompt that lets the LLM merge everything
    ctx_json = json.dumps(ctx, indent=2)

    system = (
    "You are a senior HR copy-writer. Produce a polished, ATS-ready job description in Markdown **only** "
    "(no code fences, HTML, or commentary).\n"
    "\n"
    "Begin with a 4-line header block in this order — one line each:\n"
    "Job Description: <Job Title>\n"
    "<Company Name>\n"
    "<Job Type>\n"
    "<Location>\n"
    "\n"
    "Leave one blank line, then **if** *AboutCompany* is supplied add:\n"
    "### About the Company\n"
    "(insert text)\n"
    "\n"
    "After that, write the rest of the JD, mirroring the headings / bullet style in *CompanyExamples*.\n"
    "Keep total length ≈ 450 words and preserve every critical requirement from *DraftJD* and *HiringManagerJSON*."
    )

    prompt = textwrap.dedent(
    f'''
    ## Inputs
    ### HiringManagerJSON
    {ctx_json}

    ### AboutCompany (optional)
    {about_company or 'N/A'}

    ### DraftJD
    {draft_jd}

    ### CompanyExamples
    {examples}

    ## Task
    Using the guidelines in the *system* prompt, output the **final** job description in Markdown only
    (no code fences, no extra explanations). Make sure the top block contains the four required lines
    in the order specified, then the “About the Company” section if present, then the JD body.
    '''
    )


    jd_markdown = gpt_generate(prompt, system, max_tokens=900).strip()

    return clean_markdown(jd_markdown)

# ---------------------------------------------------------------------------
# Feedback revision helper
# ---------------------------------------------------------------------------

def revise_final_jd(current_jd: str, feedback: str, ctx: dict) -> str:
    """Apply manager feedback while preserving structure."""

    system = (
        "You are an HR copy‑writer. Apply the feedback below to the JD while "
        "keeping tone, structure, and Markdown formatting. Output Markdown only."
    )
    prompt = textwrap.dedent(
        f"""
        ### CurrentJD
        {current_jd}

        ### Feedback
        {feedback}

        ### HiringManagerJSON
        {json.dumps(ctx, indent=2)}

        ### Task
        Return the revised JD.
        """
    )

    return clean_markdown(gpt_generate(prompt, system, max_tokens=650).strip())
