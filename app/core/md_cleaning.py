from __future__ import annotations

"""Utility: sanitize Markdown returned by the LLM before rendering.

Typical issues we strip:
  • Leading code‑fence inserted by the model, e.g. "```markdown" or plain "```".
  • Trailing closing fence "```".
  • Stray <div>…</div> wrappers.
  • Leading/trailing whitespace.

Call `clean_markdown()` on any LLM output before saving or displaying.
"""

import re

# Pre‑compiled regex patterns -------------------------------------------------
_FENCE_START = re.compile(r"^\s*```[a-zA-Z0-9]*\s*\n", flags=re.MULTILINE)
_FENCE_END = re.compile(r"\n\s*```\s*$", flags=re.MULTILINE)
_DIV_TAGS = re.compile(r"</?div[^>]*>", flags=re.IGNORECASE)


def clean_markdown(md: str | None) -> str:
    """Return *md* stripped of leading/trailing code fences & stray <div> tags."""
    if not md:
        return ""

    out = _FENCE_START.sub("", md)
    out = _FENCE_END.sub("", out)
    out = _DIV_TAGS.sub("", out)

    return out.strip()
