from .local_model import generate
from .md_cleaning import clean_markdown

def draft(ctx):
    system = "You are an HR assistant who writes concise draft job descriptions."
    prompt = f"""
    Write a draft JD for **{ctx['job_title']}**.
    Job Details to be added on the JD: 1) Company Name: {ctx['company_name']} ; Job Type: {ctx['job_type']} ; Job Location: {ctx['job_location']}.  
    Hiring manager Context: {ctx['context']}; Experience: {ctx['years_exp']} yrs.
    Headings: Responsibilities, Required Skills, Preferred Skills, Benefits. If notjing is mentioned then leave out that detail. It should not contain any unknown blocks for user to fill.
    Note: Please Return the Job derscription in Markdown format as it is going to shown on the UI in that and markdown block.
    """
    out= generate(prompt, system=system, max_tokens=1000)
    draft_jd= clean_markdown(out)
    return draft_jd
