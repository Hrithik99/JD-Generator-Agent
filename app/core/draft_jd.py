from .local_model import generate

def draft(ctx):
    system = "You are an HR assistant who writes concise draft job descriptions."
    prompt = f"""
    Write a draft JD for **{ctx['job_title']}**.
    Hiring manager Context: {ctx['context']}; Experience: {ctx['years_exp']} yrs.
    Headings: Responsibilities, Required Skills, Preferred Skills, Benefits.
    """
    return generate(prompt, system=system, max_tokens=1000)
