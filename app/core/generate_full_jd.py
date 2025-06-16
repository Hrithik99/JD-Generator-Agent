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
    """
    Merge the strong draft with About-Company (optional) and tone examples,
    returning a polished Markdown JD.  The DraftJD is **authoritative**: never
    remove or contradict its content—only refine, re-order, or expand.
    """

    # 1⃣  Optional About-Company section
    company_url = company_url or ctx.get("company_url") or os.getenv("COMPANY_URL")
    about_company = ""
    if company_url:
        try:
            from .generate_full_jd import generate_about_company
            about_company = generate_about_company(company_url)
        except Exception as exc:  # pragma: no cover
            print(f"[warn] About-company generation failed: {exc}")

    # 2⃣  Retrieve similar JDs for tone
    examples = retrieve(draft_jd, corpus_texts, index, k=k)

    # 3⃣  Build prompt
    ctx_json = json.dumps(ctx, indent=2)
    system = (
        "You are a senior HR copy-writer.  Output Markdown only – no HTML, no code "
        "fences, no explanations.  Follow the template exactly. "
        "Do not add ant additional fabricated or generic PII information like email or instruction if not specifically mentioned in the inputs provided."
    )

    template = textwrap.dedent("""\
        # {job_title}

        {company_name}  
        {job_type}  
        {location}

        {about_block}

        ## Responsibilities
        (retain, polish and extrapolate bullets from DraftJD and simlar job descirption provided in exaples, if any)

        ## Required Skills
        (retain & polish bullets from DraftJD and simlar job descirption provided in exaples, if any)

        ## Preferred Skills
        (retain & polish bullets from DraftJD and simlar job descirption provided in exaples, if any)

        ## Benefits
        (retain & polish bullets from DraftJD, if any)
    """)

    prompt = textwrap.dedent(f"""
        ### Context
        **HiringManagerJSON**
        {ctx_json}

        ### Template
        Fill this template strictly.  Replace the bracketed placeholders.  If a
        section does not exist in DraftJD, omit that whole section header.

        ```markdown
        {template}
        ```

        ### AboutCompany (optional)
        Replace {{about_block}} above with this, *verbatim*, under a heading
        `## About the Company` – otherwise delete {{about_block}}.

        {about_company or 'N/A'}

        ### DraftJD  (authoritative – keep all content)
        {draft_jd}

        ### CompanyExamples  (tone/style only)
        {examples}

        ### Task
        1. Copy every bullet or sentence from DraftJD into the matching section.
        2. You may re-phrase for clarity and add short, logical expansions to skillset from examples [if the match is high].
        3. **Never remove a requirement from DraftJD.**
        4. If any detail (email, address, team info) is not given, delete that line
        – do **NOT** create placeholders.
        5. Return Markdown only.
    """)

    jd_markdown = clean_markdown(gpt_generate(prompt, system, max_tokens=900).strip())
    print(jd_markdown)
    return jd_markdown

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
