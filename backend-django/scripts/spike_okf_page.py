"""Spike #94 (throwaway): can the Agent turn a book title into a valid OKF v0.2 page?

Usage (from backend-django/):
    OPENROUTER_API_KEY=... uv run --with pyyaml python scripts/spike_okf_page.py [out_dir]
"""

import json
import os
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

import yaml

MODEL = os.getenv("SPIKE_MODEL", "deepseek/deepseek-v4.1-flash")
URL = "https://openrouter.ai/api/v1/chat/completions"

HEADINGS = {
    "pl": ["Streszczenie", "Postacie", "Miejsca", "Wątki i motywy"],
    "en": ["Summary", "Characters", "Places", "Themes"],
}

REQUESTS = [
    "Dodaj książkę „Ostatnie życzenie”",
    "Dodaj książkę „Lalka”",
    "Dodaj książkę „Solaris”",
    "Add the book “Dune”",
    "Add the book “The Hobbit”",
]

PROMPT = """You write one page of a private book wiki in Open Knowledge Format (OKF) v0.2.
Return ONLY the raw Markdown document (no code fences, no commentary).

Write in the language of the user's request. Polish request -> Polish page, English -> English.

The document starts with YAML frontmatter between `---` lines with exactly these keys:
  type: book
  title: <book title>
  description: <one sentence>
  author: <author name>
  generated: {{ by: storyshelf-agent/{model}, at: <now, UTC ISO 8601, e.g. 2026-10-03T12:00:00Z> }}

After the frontmatter, the body has exactly these four level-2 sections, in this order:
  Polish:  ## Streszczenie / ## Postacie / ## Miejsca / ## Wątki i motywy
  English: ## Summary / ## Characters / ## Places / ## Themes
Under Characters and Places, write a bullet list:
`- [Name](/characters/<slug>--<book-slug>.md) — role in this book` (places use /places/).
Slugs are lowercase ASCII with hyphens.
If you do not know the book, return a page with type: book, the title and empty sections.

User request: {request}
"""


def call(request: str) -> tuple[str, dict, float]:
    body = json.dumps(
        {
            "model": MODEL,
            "messages": [{"role": "user", "content": PROMPT.format(model=MODEL, request=request)}],
            "usage": {"include": True},
        }
    ).encode()
    req = urllib.request.Request(
        URL,
        data=body,
        headers={
            "Authorization": f"Bearer {os.environ['OPENROUTER_API_KEY']}",
            "Content-Type": "application/json",
        },
    )
    start = time.monotonic()
    with urllib.request.urlopen(req, timeout=120) as resp:
        envelope = json.loads(resp.read())
    latency = time.monotonic() - start
    return envelope["choices"][0]["message"]["content"], envelope.get("usage", {}), latency


def validate(page: str) -> list[str]:
    """Return a list of problems (empty = valid)."""
    problems = []
    text = page.strip()
    if text.startswith("```"):
        problems.append("wrapped in code fence")
        text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
    if not text.startswith("---\n"):
        return problems + ["no frontmatter"]
    try:
        _, fm_raw, body = text.split("---", 2)
        fm = yaml.safe_load(fm_raw)
    except (ValueError, yaml.YAMLError) as exc:
        return problems + [f"frontmatter parse: {exc}"]
    if not isinstance(fm, dict):
        return problems + ["frontmatter not a mapping"]

    if fm.get("type") != "book":
        problems.append(f"type={fm.get('type')!r}")
    for key in ("title", "description", "author"):
        if not fm.get(key):
            problems.append(f"missing {key}")
    gen = fm.get("generated")
    if not isinstance(gen, dict) or not gen.get("by"):
        problems.append(f"bad generated: {gen!r}")
    else:
        at = gen.get("at")
        try:
            # YAML may already parse it into a datetime
            if not isinstance(at, datetime):
                datetime.fromisoformat(str(at).replace("Z", "+00:00"))
        except ValueError:
            problems.append(f"generated.at not ISO 8601: {at!r}")

    found = [line[3:].strip() for line in body.splitlines() if line.startswith("## ")]
    if found not in HEADINGS.values():
        problems.append(f"headings={found}")
    return problems


def main() -> None:
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    out_dir.mkdir(parents=True, exist_ok=True)
    print("| # | request | ok | problems | latency s | tokens in/out | cost $ |")
    print("|---|---|---|---|---|---|---|")
    for i, request in enumerate(REQUESTS, 1):
        try:
            page, usage, latency = call(request)
        except Exception as exc:  # spike: record any failure as a finding
            print(f"| {i} | {request} | ERR | {exc} | | | |")
            continue
        (out_dir / f"page{i}.md").write_text(page)
        problems = validate(page)
        print(
            f"| {i} | {request} | {'yes' if not problems else 'no'} | {'; '.join(problems)} "
            f"| {latency:.1f} | {usage.get('prompt_tokens')}/{usage.get('completion_tokens')} "
            f"| {usage.get('cost')} |"
        )


if __name__ == "__main__":
    main()
