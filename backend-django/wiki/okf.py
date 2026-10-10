"""OKF v0.2 Pages: parsing, validation, Paths and empty Templates. No DB, no DRF."""

import re
import unicodedata

import yaml

DIRS = {"book": "books", "character": "characters", "place": "places", "universe": "universes"}

# Szablon: `##` headings every Page of a type must keep (same as frontend/src/wiki.ts)
TEMPLATES = {
    "book": ["Streszczenie", "Postacie", "Miejsca", "Wątki i motywy"],
    "character": ["Opis", "Rola w książce", "Powiązania"],
    "place": ["Opis", "Rola w książce"],
    "universe": ["Opis"],
}

# Opening `---`, optional YAML block, closing `---`; LF or CRLF
FRONTMATTER = re.compile(r"^---\r?\n(?:([\s\S]*?)\r?\n)?---(?:\r?\n|$)")


class OKFError(ValueError):
    """Message for the User; `field` is the API error key."""

    def __init__(self, message, field="content"):
        super().__init__(message)
        self.field = field


def parse(content):
    match = FRONTMATTER.match(content)
    if not match:
        raise OKFError("Invalid frontmatter: Missing frontmatter")
    try:
        frontmatter = yaml.safe_load(match[1] or "")
    except yaml.YAMLError as e:
        raise OKFError(f"Invalid frontmatter: {getattr(e, 'problem', None) or e}") from e
    except RecursionError as e:
        raise OKFError("Invalid frontmatter: too deeply nested") from e
    if frontmatter is None:
        frontmatter = {}
    if not isinstance(frontmatter, dict):
        raise OKFError("Invalid frontmatter: not a mapping")
    return frontmatter, content[match.end():].lstrip()


def validate(content, page_type):
    """Frontmatter of a valid Page, or OKFError with the first problem."""
    frontmatter, body = parse(content)
    if "type" not in frontmatter:
        raise OKFError("Missing type")
    # type picks the Path directory, so changing it would break the Page identity
    if frontmatter["type"] != page_type:
        raise OKFError("Page type can't change")
    title = frontmatter.get("title")
    if not isinstance(title, str) or not title.strip():
        raise OKFError("Missing title")
    lines = {line.strip() for line in body.splitlines()}
    missing = [h for h in TEMPLATES[page_type] if f"## {h}" not in lines]
    if missing:
        raise OKFError(f"Missing template headings: {', '.join(missing)}")
    return frontmatter


def slugify(text):
    """ASCII slug for Paths; 'Krew elfów' → 'krew-elfow' (same rules as wiki.ts)."""
    text = unicodedata.normalize("NFD", text.replace("ł", "l").replace("Ł", "L"))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def page_path(page_type, title, book=None):
    """Characters and places are per book for now: '/characters/geralt--krew-elfow.md'."""
    slug = slugify(title)
    if not slug:
        raise OKFError("Title needs at least one letter or digit", field="title")
    if page_type in ("character", "place"):
        slug = f"{slug}--{book.removeprefix('/books/').removesuffix('.md')}"
    return f"/{DIRS[page_type]}/{slug}.md"


def render_template(page_type, meta):
    """Empty Page: frontmatter with `status: draft`, then the Template headings."""
    fields = {"type": page_type, **{k: v for k, v in meta.items() if v is not None}}
    fields["status"] = "draft"
    frontmatter = yaml.safe_dump(fields, allow_unicode=True, sort_keys=False)
    body = "\n".join(f"## {h}\n" for h in TEMPLATES[page_type])
    return f"---\n{frontmatter}---\n\n{body}"
