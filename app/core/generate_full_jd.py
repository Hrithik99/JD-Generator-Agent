# generate_full_jd.py
from .rag_utils import retrieve
from .openai_model import generate as gpt_generate
import json, textwrap

def finalize(draft_jd: str,
             ctx: dict,                # ← pass the full JSON payload here
             corpus_texts: list[str],
             index,
             k: int = 3) -> str:
    """
    Create the final company‑aligned JD.

    Parameters
    ----------
    draft_jd : str
        The draft job description produced by the local model.
    ctx : dict
        Entire JSON payload containing job_title, hiring manager context, years_exp, etc.
    corpus_texts : list[str]
        Raw text of historical company JDs.
    index : faiss.Index
        FAISS index built over corpus_texts.
    k : int
        Number of similar JDs to retrieve for RAG context.
    """
    # 1. Retrieve top‑k similar company examples
    examples = retrieve(draft_jd, corpus_texts, index, k=k)

    # 2. Serialize ctx for transparency in the prompt
    ctx_json = json.dumps(ctx, indent=2)

    # 3. Compose the system & user prompt
    system = (
        "You are a senior HR copy‑writer. Using the draft JD, hiring‑manager "
        "inputs (JSON), and prior company JDs, craft a polished job description "
        "that matches the company's tone, is inclusive, and retains all critical "
        "requirements. Keep headings and limit to ~450 words."
    )

    prompt = textwrap.dedent(f"""
                             
        ### About the Company:
                                
        ### Hiring‑Manager Inputs (JSON)
        {ctx_json}

        ### Draft JD
        {draft_jd}

        ### Company Examples
        {examples}

        ### Task
        Produce the final, company‑aligned JD.
    """)

    return gpt_generate(prompt, system)


def revise_final_jd(current_jd: str, feedback: str, ctx: dict) -> str:
    """Use GPT‑4o to apply feedback on the final JD."""
    system = ("You are an HR copy‑writer. Apply the hiring manager's feedback "
              "to the job description but keep company tone and structure.")
    prompt = f"""
    ### Current JD
    {current_jd}

    ### Feedback
    {feedback}

    ### Hiring‑Manager Inputs (JSON)
    {json.dumps(ctx, indent=2)}

    ### Task
    Return the revised, polished JD.
    """
    return gpt_generate(prompt, system, max_tokens=650)
