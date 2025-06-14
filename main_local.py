from input_forms import collect_inputs, save_json
from app.core.draft_jd import draft
import json
from app.core.generate_full_jd import finalize
from app.core.rag_utils import load_corpus, build_or_load_faiss
from app.core.local_model import generate as local_generate
from app.core.openai_model import generate as gpt_generate

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

# ──────────────────────────────────────────────────────────────────────────
def main():
    # 0. Collect hiring‑manager inputs
    ctx = collect_inputs()

    # 1. Ask if they want a quick draft or skip to final
    choice = input("\nType 'draft' for quick preview or 'final' to jump straight "
                   "to company‑aligned JD: ").strip().lower()
    
    

    if choice == "draft":
        # ── Draft JD via local model + feedback loop ──────────────────────
        jd = draft(ctx)
        print("\n── Draft JD ──\n", jd)

        while True:
            fb = input("\nFeedback or 'create': ").strip().lower()
            if fb == "create":
                break
            jd = local_generate(
                fb + "\n\n" + jd,
                system="Revise the draft JD accordingly.",
                max_tokens=1000)
            print("\n── Updated Draft ──\n", jd)

        ctx["draft_jd"] = jd

    else:  # choice == "final"
        # Skip local model; build a minimal draft from inputs for context
        auto_draft = f"Role: {ctx['job_title']}\Hiring Manager Context about the role: {ctx['context']}\n"\
                     f"Years Exp: {ctx['years_exp']}"
        ctx["draft_jd"] = auto_draft
        print("\n(Skipping draft loop, going straight to final JD…)")

    save_json(ctx)  # Persist inputs + (possibly auto) draft JD

    # 2. Build RAG context & generate first company‑aligned JD via GPT‑4o
    _, texts = load_corpus("data/corpus")
    index = build_or_load_faiss(texts)
    full_jd = finalize(ctx["draft_jd"], ctx, texts, index)
    print("\n📄 FINAL JD (v1)\n", full_jd)

    # 3. Final approval / revision loop with GPT‑4o
    version = 1
    while True:
        fb = input("\nType feedback to revise, or 'approve' to finish: ").strip()
        if fb.lower() == "approve":
            break
        version += 1
        full_jd = revise_final_jd(full_jd, fb, ctx)
        print(f"\n📄 FINAL JD (v{version})\n", full_jd)

    # 4. Save approved JD
    with open("final_jd.txt", "w", encoding="utf-8") as f:
        f.write(full_jd)
    print("✅ Saved to final_jd.txt")



if __name__ == "__main__":
    main()
