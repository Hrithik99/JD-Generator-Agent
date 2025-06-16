from .local_model import generate
from .md_cleaning import clean_markdown,clean_llm_json
import textwrap,json




def summarize_revision_change(old_draft: str, new_draft: str, user_input: str, job_title: str) -> str:
    """Use LLM to summarize what changed in a human-readable 1-liner for history tracking."""
    prompt = f"""
You are a helpful HR assistant.

A hiring manager working on a `{job_title}` role gave the following input:
"{user_input}"

Here is the previous draft JD:
{old_draft}

And here is the updated draft JD:
{new_draft}

Summarize the revision in a single bullet point that describes what was added, improved, or changed.
Be specific (e.g., "Added Kubernetes and Airflow for workflow orchestration").
Only return the summary point — no introduction, no extra formatting.
"""

    return generate(prompt.strip(), system="Summarize the JD revision clearly.").strip()


def draft(ctx: dict) -> dict:
    """
    Generate an initial JD draft and follow-up suggestion.

    Returns
    -------
    dict
      {
        "draft": "<markdown JD>",
        "follow_up": "<short follow-up question>"
      }
    """

    system = (
        "You are an HR assistant who writes concise, structured job descriptions "
        "and recommends improvements based on industry practices."
    )

    prompt = textwrap.dedent(f"""
        ### Task
        1. Write a draft JD for **{ctx['job_title']}** using Markdown.
        2. After crafting the JD, create a short follow-up suggestion that begins
           with: "Based on common expectations for a {ctx['job_title']} role, you might also consider including..."
           (suggest 2–3 additional skills, certifications, or responsibilities).

        ### Job Details
        - Company Name: {ctx['company_name']}
        - Job Type: {ctx['job_type']}
        - Job Location: {ctx['job_location']}
        - Experience Required: {ctx['years_exp']} yrs

        ### Hiring-Manager Context
        {ctx['context']}

        ### Format Rules
        • Use Markdown headings/bullets for the JD.  
        • Do **NOT** leave placeholders or incomplete fields.
        • If any detail (e.g., email, address, team info, location, job type) is not explicitly provided, omit that detail entirely—do NOT invent or insert placeholder text.  
        • **Output must be valid JSON**, with exactly these two keys:

        ```json
        {{
          "draft": "<markdown job description>",
          "follow_up": "<follow-up question>"
        }}
        ```
        Only return the JSON—no extra text.
    """)

    response = generate(prompt.strip(), system=system, max_tokens=1200).strip()

    # ----- Try JSON-parsing first ------------------------------------
    try:
        data = clean_llm_json(response)
        jd = clean_markdown(data.get("draft", ""))
        follow_up = data.get("follow_up", "")
        return {"draft": jd, "follow_up": follow_up}
    except json.JSONDecodeError:
        # Fallback: attempt old split approach so we don't break the flow
        parts = response.split("follow-up", maxsplit=1)
        jd = clean_markdown(parts[0].strip())
        follow_up = parts[1].strip() if len(parts) > 1 else ""
        return {"draft": jd, "follow_up": follow_up}



def revise_draft_jd(
    current_jd: str,
    input_text: str,
    ctx: dict,
    revision_summary: str = ""
) -> dict:
    """
    Revise an existing JD with new input, integrate history, and provide a follow-up
    suggestion. Returns:

      {
        "draft": "<markdown JD>",
        "follow_up": "<suggestion string>"
      }
    """

    system_prompt = (
        "You are a senior HR assistant and job-description expert. "
        "Revise the JD, preserve structure/tone, then propose missing skills. "
        "Return ONLY valid JSON."
    )

    prompt = textwrap.dedent(f"""
        ### CurrentDraftJD
        {current_jd}

        ### AdditionalInput
        {input_text}

        ### HiringContext
        {json.dumps(ctx, indent=2)}

        ### PriorRevisionsSummary
        {revision_summary}

        ### Task
        1. Update the JD using the new input.
        2. If any detail (e.g., email, address, team info, location, job type) is not explicitly provided, omit that detail entirely—do NOT invent or insert placeholder text.
        3. Keep Markdown formatting and helpful existing content.
        4. Append a follow-up message suggesting up to three missing skills/responsibilities.
           Begin that message with:
           "**Follow-Up**: Based on common expectations for a '{ctx.get('job_title','N/A')}' role, you might consider..."
        5. **Output must be valid JSON**, in the exact shape:

        ```json
        {{
          "draft": "<full markdown JD>",
          "follow_up": "<follow-up question>"
        }}
        ```

        Do NOT wrap the JSON in code fences or add extra keys.
    """)

    response = generate(prompt=prompt.strip(),
                        system=system_prompt,
                        max_tokens=1200).strip()

    # --- primary: JSON parse -----------------------------------------
    try:
        data = clean_llm_json(response)
        jd = clean_markdown(data.get("draft", ""))
        follow_up = data.get("follow_up", "")
        return {"draft": jd, "follow_up": follow_up}
    except json.JSONDecodeError:
        # --- fallback: legacy split in case model mis-formats ----------
        parts = response.split("follow-up", maxsplit=1)
        jd = clean_markdown(parts[0].strip())
        follow_up = parts[1].strip() if len(parts) > 1 else ""
        return {"draft": jd, "follow_up": follow_up}


