import click, json, datetime, pathlib

FIELDS = ["job_title", "skills", "years_exp", "education", "work_auth"]

def collect_inputs():
    ctx = {}
    for field in FIELDS:
        required = field != "work_auth"
        ctx[field] = click.prompt(
            f"{field.replace('_',' ').title()}",
            default="" if not required else None,
            show_default=False)
    return ctx

def save_json(payload):
    ts = datetime.datetime.utcnow().isoformat(timespec="seconds").replace(":", "-")
    out = pathlib.Path("data/saves") / f"draft_{ts}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2))
    return out
